import React,{useState} from 'react';
import {SafeAreaView,View,Text,TextInput,Pressable,ScrollView,StyleSheet,ActivityIndicator,Platform} from 'react-native';
import * as Haptics from 'expo-haptics';
import * as SecureStore from 'expo-secure-store';
import {StatusBar} from 'expo-status-bar';
import {requestAssessment} from './src/vcpClient';
export default function App(){
 const [gateway,setGateway]=useState('https://i-the-one-buddy-api.onrender.com');
 const [token,setToken]=useState(''),[claim,setClaim]=useState('');
 const [status,setStatus]=useState('Ready. No microphone or camera runs automatically.');
 const [data,setData]=useState(null),[busy,setBusy]=useState(false),[optin,setOptin]=useState(false);
 async function run(){
  setBusy(true);setData(null);setStatus('Collecting available evidence; this is not certification.');
  try {
   if(Platform.OS!=='web')await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
   const stored=token.trim() || await SecureStore.getItemAsync('buddy_session_token') || '';
   const result=await requestAssessment({gateway,prompt:claim,token:stored});
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
  <Text style={s.caption}>No evidence, no verification. No defined standard, no certification. No authorization, no execution.</Text>
 </ScrollView></SafeAreaView>
}
const s=StyleSheet.create({root:{flex:1,backgroundColor:'#041712'},box:{padding:20,gap:13},small:{color:'#8fdec8',letterSpacing:2},title:{fontSize:38,fontWeight:'900',color:'#7ce5bd'},caption:{fontSize:14,color:'#badad0',lineHeight:21},label:{fontSize:16,fontWeight:'700',color:'#87e8c3'},input:{borderWidth:1,borderColor:'#4a967e',borderRadius:12,color:'white',backgroundColor:'#0e2923',padding:14},primary:{backgroundColor:'#68e6b3',padding:16,borderRadius:12,alignItems:'center'},secondary:{borderColor:'#4a967e',borderWidth:1,padding:12,borderRadius:12,alignItems:'center'},action:{fontSize:16,fontWeight:'800',color:'#b3f7db'},status:{color:'#d8f1e9'},card:{borderRadius:14,backgroundColor:'#11372d',padding:14},json:{color:'#d0f0e5',fontSize:11}});
