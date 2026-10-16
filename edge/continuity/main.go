// i™ Offline Continuity (reference implementation).
// Opt-in batch uploader with append-only pending queue. No "background sync",
// no unauthenticated upload, no fictional SOURCECHAIN receipt or deletion of data.
// Acknowledged items move to .ack.jsonl; re-send after a crash may duplicate.
// Production receiver MUST deduplicate on event id.
package main

import (
 "bufio"
 "bytes"
 "context"
 "crypto/sha256"
 "encoding/hex"
 "encoding/json"
 "errors"
 "fmt"
 "io"
 "net/http"
 "net/url"
 "os"
 "path/filepath"
 "strings"
 "time"
)

type Event struct {
 ID string `json:"id"`
 Payload string `json:"payload"`
 Time string `json:"time"`
}
type Receipt struct {
 ID string `json:"id"`
 SHA256 string `json:"sha256"`
 Uploaded bool `json:"uploaded"`
}

func filename(base string) string { return base+".pending.jsonl" }
func appendLine(file string, value any) error {
 b,err:=json.Marshal(value);if err!=nil{return err}
 f,err:=os.OpenFile(file,os.O_WRONLY|os.O_CREATE|os.O_APPEND,0600);if err!=nil{return err}
 defer f.Close()
 if _,err=f.Write(append(b,'\n'));err!=nil{return err}
 return f.Sync()
}
func load(file string)([]Event,error){
 f,err:=os.Open(file);if errors.Is(err,os.ErrNotExist){return []Event{},nil};if err!=nil{return nil,err}
 defer f.Close()
 scan:=bufio.NewScanner(f);scan.Buffer(make([]byte,4096),64*1024)
 var out []Event
 for scan.Scan(){var ev Event;if err=json.Unmarshal(scan.Bytes(),&ev);err!=nil{return nil,err}
  if len(ev.ID)==0 || len(ev.Payload)>4096{return nil,errors.New("invalid queued event")}
  out=append(out,ev)}
 return out,scan.Err()
}
func enqueue(base,payload string)(Receipt,error){
 if len(payload)==0 || len(payload)>4096{return Receipt{},errors.New("payload must be 1..4096 bytes")}
 seed:=fmt.Sprintf("%d:%s",time.Now().UnixNano(),payload)
 idBytes:=sha256.Sum256([]byte(seed));id:=hex.EncodeToString(idBytes[:])
 ev:=Event{ID:id,Payload:payload,Time:time.Now().UTC().Format(time.RFC3339Nano)}
 if err:=appendLine(filename(base),ev);err!=nil{return Receipt{},err}
 checksum:=sha256.Sum256([]byte(payload))
 return Receipt{ID:id,SHA256:hex.EncodeToString(checksum[:]),Uploaded:false},nil
}
func syncQueue(ctx context.Context,base,endpoint,token string,client *http.Client)(int,error){
 u,err:=url.Parse(endpoint)
 if err!=nil || u.Scheme!="https" || u.Host=="" || u.User!=nil || u.Fragment!="" {return 0,errors.New("explicit HTTPS URL required")}
 if token==""{return 0,errors.New("explicit bearer token required")}
 events,err:=load(filename(base));if err!=nil{return 0,err}
 if len(events)==0{return 0,nil}
 sent:=0;remaining:=[]Event{}
 for i,ev:=range events {
  body,_:=json.Marshal(ev)
  req,err:=http.NewRequestWithContext(ctx,http.MethodPost,endpoint,bytes.NewReader(body))
  if err!=nil{return sent,err}
  req.Header.Set("Authorization","Bearer "+token)
  req.Header.Set("Content-Type","application/json")
  resp,err:=client.Do(req)
  if err!=nil{remaining=append(remaining,events[i:]...);break}
  io.Copy(io.Discard,io.LimitReader(resp.Body,4096));resp.Body.Close()
  if resp.StatusCode<200 || resp.StatusCode>=300{
   remaining=append(remaining,events[i:]...);break
  }
  // Only explicitly acknowledged 2xx HTTP requests are archived.
  if err:=appendLine(base+".ack.jsonl",ev);err!=nil{return sent,err}
  sent++
 }
 // Safe atomic replacement; never overwrite the audit archive.
 tmp:=filename(base)+".tmp"
 f,err:=os.OpenFile(tmp,os.O_WRONLY|os.O_CREATE|os.O_TRUNC,0600);if err!=nil{return sent,err}
 for _,ev:=range remaining {b,_:=json.Marshal(ev);if _,err=f.Write(append(b,'\n'));err!=nil{f.Close();return sent,err}}
 if err=f.Sync();err!=nil{f.Close();return sent,err}
 f.Close()
 if err=os.Rename(tmp,filename(base));err!=nil{return sent,err}
 if len(remaining)>0{return sent,fmt.Errorf("%d events remain queued; transport unavailable or rejected",len(remaining))}
 return sent,nil
}
func main(){
 if len(os.Args)<3{fmt.Fprintln(os.Stderr,"usage: continuity {enqueue|status|sync} DATA_DIR [payload]");os.Exit(2)}
 action:=os.Args[1]
 dir:=os.Args[2]
 if err:=os.MkdirAll(dir,0700);err!=nil{panic(err)}
 base:=filepath.Join(dir,"i-continuity")
 switch action {
 case "enqueue":
  if len(os.Args)!=4{panic("enqueue requires one payload argument")}
  r,err:=enqueue(base,os.Args[3]);if err!=nil{panic(err)}
  b,_:=json.Marshal(r);fmt.Println(string(b))
 case "status":
  events,err:=load(filename(base));if err!=nil{panic(err)}
  fmt.Printf("{\"pending\":%d,\"gateway_connected\":false}\n",len(events))
 case "sync":
  endpoint:=os.Getenv("I_CONTINUITY_SYNC_URL")
  token:=os.Getenv("I_CONTINUITY_BEARER_TOKEN")
  if strings.TrimSpace(endpoint)=="" {panic("I_CONTINUITY_SYNC_URL missing; no default network gateway")}
  ctx,cancel:=context.WithTimeout(context.Background(),25*time.Second);defer cancel()
  client:=&http.Client{Timeout:8*time.Second,CheckRedirect:func(_ *http.Request,_ []*http.Request)error{return http.ErrUseLastResponse}}
  count,err:=syncQueue(ctx,base,endpoint,token,client)
  if err!=nil{fmt.Fprintf(os.Stderr,"accepted=%d: %v\n",count,err);os.Exit(1)}
  fmt.Printf("{\"acknowledged\":%d,\"claim\":\"HTTP accepted, no blockchain/hardware attestation\"}\n",count)
 default:panic("unknown command")
 }
}
