import React,{useState} from 'react';
import {signIn,refresh,signOut} from './src/auth';
import {validateCertificate} from './src/certificate';
import {SafeAreaView,View,Text,TextInput,Pressable,ScrollView,StyleSheet,ActivityIndicator,Platform} from 'react-native';
import * as Haptics from 'expo-haptics';
import * as SecureStore from 'expo-secure-store';
import {StatusBar} from 'expo-status-bar';
import {requestAssessment} from './src/vcpClient';
export default function App(){
 const [gateway,setGateway]=useState('https://i-the-one-buddy-api.onrender.com');
 const [authURL,setAuthURL]=useState(''),[publishableKey,setPublishableKey]=useState(''),[email,setEmail]=useState(''),[password,setPassword]=useState('');
 const [iceURL,setIceURL]=useState(''),[certificateJSON,setCertificateJSON]=useState('');
 const [token,setToken]=useState(''),[claim,setClaim]=useState('');
 const [status,setStatus]=useState('Ready. No microphone or camera runs automatically.');
 const [data,setData]=useState(null),[busy,setBusy]=useState(false),[optin,setOptin]=useState(false);
 async function login(){
  setBusy(true);
  try{
   const session=await signIn({url:authURL,key:publishableKey,email,password});
   await SecureStore.setItemAsync('buddy_session_token',session.access_token);
   await SecureStore.setItemAsync('buddy_refresh_token',session.refresh_token);
   setPassword('');setToken('');setStatus('Signed in to Buddy. Session stored in device-protected storage.');
  }catch(e){setStatus(String(e.message))}finally{setBusy(false)}
 }
 async function logout(){
  setBusy(true);
  try{
   const active=await SecureStore.getItemAsync('buddy_session_token');
   if(active&&authURL&&publishableKey)await signOut({url:authURL,key:publishableKey,access_token:active});
  }catch(e){setStatus('Remote sign-out unavailable; local credentials cleared.');}
  finally{
   await SecureStore.deleteItemAsync('buddy_session_token');
   await SecureStore.deleteItemAsync('buddy_refresh_token');
   setBusy(false);setStatus('Local Buddy session cleared.');
  }
 }
 async function checkCertificate(){
  setBusy(true);
  try{
   const result=await validateCertificate({url:iceURL,certificate:JSON.parse(certificateJSON)});
   setStatus(result.state+' · '+result.message);
  }catch(e){setStatus('Certificate validation unavailable: '+String(e.message))}finally{setBusy(false)}
 }
 async function run(){
  setBusy(true);setData(null);setStatus('Collecting available evidence; this is not certification.');
  try {
   if(Platform.OS!=='web')await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
   const stored=token.trim() || await SecureStore.getItemAsync('buddy_session_token') || '';
   let result;
   try{result=await requestAssessment({gateway,prompt:claim,token:stored})}
   catch(error){
    const refreshToken=await SecureStore.getItemAsync('buddy_refresh_token');
    if(!refreshToken || !authURL || !publishableKey || !String(error.message).includes('HTTP 401'))throw error;
    const newSession=await refresh({url:authURL,key:publishableKey,refresh_token:refreshToken});
    await SecureStore.setItemAsync('buddy_session_token',newSession.access_token);
    await SecureStore.setItemAsync('buddy_refresh_token',newSession.refresh_token);
    result=await requestAssessment({gateway,prompt:claim,token:newSession.access_token});
   }
   setData(result);
   setStatus(result.status+' · NOT CERTIFIED');
   if(Platform.OS!=='web')await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  }catch(e){
   setStatus(String(e.message||e));
   if(Platform.OS!=='web')await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
  }finally{setBusy(false)}
 }
 async function save(){
  if(!optin){setStatus('Select consent before storing credentials on this device');return}
  if(!token.trim()){setStatus('Paste a valid Buddy session token first');return}
  await SecureStore.setItemAsync('buddy_session_token',token.trim());
  setToken('');setStatus('Session token stored in OS-protected application storage. Not a biometric identity or ICE key.');
 }
 return <SafeAreaView style={s.root}><StatusBar style="light"/><ScrollView contentContainerStyle={s.box}>
  <Text style={s.small}>i™ · JUST ASK BUDDY™</Text><Text style={s.title}>🧾 THE ONE</Text>
  <Text style={s.caption}>Peekaboo. I see you. You control when sensing begins.</Text>
  <Text style={s.caption}>No automatic ambient recording. No independent certification on this screen.</Text>
  <Text style={s.label}>Buddy identity sign-in</Text>
  <TextInput style={s.input} accessibilityLabel="Supabase Auth URL" placeholder="https://your-project.supabase.co" placeholderTextColor="#91ada6" value={authURL} onChangeText={setAuthURL} autoCapitalize="none"/>
  <TextInput style={s.input} accessibilityLabel="Public authentication key" placeholder="Supabase publishable key" placeholderTextColor="#91ada6" value={publishableKey} onChangeText={setPublishableKey} autoCapitalize="none"/>
  <TextInput style={s.input} accessibilityLabel="Email" placeholder="Email" placeholderTextColor="#91ada6" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none"/>
  <TextInput style={s.input} accessibilityLabel="Password" placeholder="Password" placeholderTextColor="#91ada6" value={password} onChangeText={setPassword} secureTextEntry/>
  <Pressable style={s.primary} onPress={login} disabled={busy}><Text style={s.action}>Sign in to Buddy</Text></Pressable>
  <Pressable style={s.secondary} onPress={logout} disabled={busy}><Text style={s.action}>Sign out</Text></Pressable>
  <Text style={s.label}>Private HTTPS Buddy gateway</Text>
  <TextInput accessibilityLabel="Gateway address" value={gateway} onChangeText={setGateway} autoCapitalize="none" style={s.input}/>
  <Text style={s.label}>Buddy session token (optional if securely saved)</Text>
  <TextInput accessibilityLabel="Buddy session" value={token} onChangeText={setToken} secureTextEntry autoCapitalize="none" style={s.input} placeholder="Paste Buddy JWT" placeholderTextColor="#91ada6"/>
  <Pressable accessibilityRole="checkbox" accessibilityState={{checked:optin}} onPress={()=>setOptin(!optin)}><Text style={s.caption}>{optin?'☑':'☐'} I consent to store my session on this device.</Text></Pressable>
  <Pressable style={s.secondary} onPress={save}><Text style={s.action}>Store session securely</Text></Pressable>
  <Text style={s.label}>Ask Buddy to investigate</Text><TextInput accessibilityLabel="Claim" style={[s.input,{height:120,textAlignVertical:'top'}]} multiline value={claim} onChangeText={setClaim} placeholder="Enter a factual claim..." placeholderTextColor="#91ada6"/>
  <Pressable style={s.primary} disabled={busy} onPress={run}>{busy?<ActivityIndicator color="#00251e"/>:<Text style={[s.action,{color:'#02261c'}]}>Run VCP Assessment</Text>}</Pressable>
  <Text accessibilityRole="alert" style={s.status}>{status}</Text>
  {data&&<View style={s.card}><Text style={s.label}>NOT CERTIFIED</Text><Text style={s.caption}>Status: {data.status}</Text><Text selectable style={s.json}>{JSON.stringify(data.record,null,2)}</Text></View>}
  <Text style={s.label}>Independent ICE certificate status (optional)</Text>
  <TextInput style={s.input} accessibilityLabel="ICE verification URL" placeholder="HTTPS private ICE verifier" placeholderTextColor="#91ada6" value={iceURL} onChangeText={setIceURL} autoCapitalize="none"/>
  <TextInput style={[s.input,{height:90}]} accessibilityLabel="Certificate JSON" multiline placeholder="Paste certificate JSON" placeholderTextColor="#91ada6" value={certificateJSON} onChangeText={setCertificateJSON}/>
  <Pressable style={s.secondary} onPress={checkCertificate} disabled={busy}><Text style={s.action}>Check ICE certificate status</Text></Pressable>
  <Text style={s.caption}>No evidence, no verification. No defined standard, no certification. No authorization, no execution.</Text>
 </ScrollView></SafeAreaView>
}
const s=StyleSheet.create({root:{flex:1,backgroundColor:'#041712'},box:{padding:20,gap:13},small:{color:'#8fdec8',letterSpacing:2},title:{fontSize:38,fontWeight:'900',color:'#7ce5bd'},caption:{fontSize:14,color:'#badad0',lineHeight:21},label:{fontSize:16,fontWeight:'700',color:'#87e8c3'},input:{borderWidth:1,borderColor:'#4a967e',borderRadius:12,color:'white',backgroundColor:'#0e2923',padding:14},primary:{backgroundColor:'#68e6b3',padding:16,borderRadius:12,alignItems:'center'},secondary:{borderColor:'#4a967e',borderWidth:1,padding:12,borderRadius:12,alignItems:'center'},action:{fontSize:16,fontWeight:'800',color:'#b3f7db'},status:{color:'#d8f1e9'},card:{borderRadius:14,backgroundColor:'#11372d',padding:14},json:{color:'#d0f0e5',fontSize:11}});
