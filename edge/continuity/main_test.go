package main
import("path/filepath";"testing")
func TestEnqueue(t *testing.T){
 base:=filepath.Join(t.TempDir(),"test")
 r,err:=enqueue(base,"hello")
 if err!=nil||r.Uploaded{t.Fatal(err)}
 rows,err:=load(filename(base))
 if err!=nil||len(rows)!=1||rows[0].Payload!="hello"{t.Fatal("queue integrity failed")}
}
