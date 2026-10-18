import {test} from 'node:test';
import assert from 'node:assert/strict';
import {creerStockage} from '../src/pas_communs/navigateur/stockage.mjs';
const dossiers=new Map(),bases=new Map();let echouerActivation=false;
const racine={async getDirectoryHandle(nom){
  if(!dossiers.has(nom))dossiers.set(nom,new Map());
  const fichiers=dossiers.get(nom);
  return {async getFileHandle(nom,{create=false}={}){
    if(!fichiers.has(nom)){if(!create)throw new Error('absent');fichiers.set(nom,new Uint8Array());}
    return {async getFile(){return new Blob([fichiers.get(nom)]);},async createSyncAccessHandle(){
      let contenu=fichiers.get(nom);
      return {write(bytes,{at}){const suivant=new Uint8Array(Math.max(contenu.length,at+bytes.length));suivant.set(contenu);suivant.set(bytes,at);contenu=suivant;return bytes.length;},
        truncate(n){contenu=contenu.slice(0,n);},flush(){fichiers.set(nom,contenu);},close(){}};
    }};
  },async *entries(){for(const nom of fichiers.keys())yield [nom,{}];},async removeEntry(nom){fichiers.delete(nom);}};
}};
Object.defineProperty(globalThis,'navigator',{value:{storage:{getDirectory:async()=>racine}},configurable:true});
globalThis.indexedDB={open(nom){
  const requete={};queueMicrotask(()=>{
    const nouvelle=!bases.has(nom);if(nouvelle)bases.set(nom,new Map());const valeurs=bases.get(nom);
    requete.result={createObjectStore(){},close(){},transaction(store,mode){
      const transaction={objectStore(){return {
        get(cle){const lecture={};queueMicrotask(()=>{lecture.result=valeurs.get(cle);lecture.onsuccess?.();});return lecture;},
        put(valeur,cle){queueMicrotask(()=>{
          if(echouerActivation){transaction.error=new Error('transaction annulée');transaction.onabort?.();}
          else{valeurs.set(cle,structuredClone(valeur));transaction.oncomplete?.();}
        });},
      };}};return transaction;
    }};if(nouvelle)requete.onupgradeneeded?.();requete.onsuccess?.();
  });return requete;
}};
const pp={application:'petits-pas',database:'pp-idb',repertoire:'pp-opfs',base:'carnet.sqlite3',legacy:true};
const chrs={application:'pas-a-pas-accompagnement',database:'chrs-idb',repertoire:'chrs-opfs',base:'accompagnement.sqlite3'};
async function valeurs(profil,texte){
  const donnees={[profil.base]:new TextEncoder().encode(texte),'secret-key':new Uint8Array([1,2,3])};
  const files={};for(const [nom,bytes] of Object.entries(donnees))files[nom]={size:bytes.length,hash:Buffer.from(await crypto.subtle.digest('SHA-256',bytes)).toString('hex')};
  return [{files,bytes:Object.values(donnees).reduce((s,b)=>s+b.length,0)},nom=>donnees[nom]];
}
async function lire(s,profil,recovery=false){const etat=await s.load('v',recovery);return new TextDecoder().decode(await etat.read(etat.files[profil.base]));}
test('espaces produits, chemins et essais indépendants',async()=>{
  const a=creerStockage(pp,'/'),b=creerStockage(chrs,'/'),c=creerStockage(chrs,'/autre/');
  await a.save(...await valeurs(pp,'école'),'v1');await b.save(...await valeurs(chrs,'personnes'),'v1');await c.save(...await valeurs(chrs,'autres'),'v1');
  assert.equal(await lire(a,pp),'école');assert.equal(await lire(b,chrs),'personnes');assert.equal(await lire(c,chrs),'autres');
  a.configurerEspace(true);assert.equal(await a.load('v'),null);a.configurerEspace(false);assert.equal(await lire(a,pp),'école');
});
test('échec avant activation et transaction annulée conservent le dernier état',async()=>{
  const s=creerStockage(chrs,'/reprise/');await s.save(...await valeurs(chrs,'ancien'),'v1');
  await assert.rejects(s.save(...await valeurs(chrs,'nouveau'),'v1','before-activate'));
  assert.equal(await lire(s,chrs),'ancien');
  echouerActivation=true;
  try{await assert.rejects(s.save(...await valeurs(chrs,'nouveau'),'v1'));}finally{echouerActivation=false;}
  assert.equal(await lire(s,chrs),'ancien');
  await s.save(...await valeurs(chrs,'nouveau'),'v2');assert.equal(await lire(s,chrs),'nouveau');assert.equal(await lire(s,chrs,true),'ancien');
});
test('manifestes étrangers refusés et historiques Petits Pas lisibles',async()=>{
  const original=creerStockage(pp,'/legacy/');await original.save(...await valeurs(pp,'historique'),'v1');
  const etranger=creerStockage({...chrs,database:pp.database,repertoire:pp.repertoire},'/legacy/');
  await assert.rejects(etranger.load('v'),/Manifeste local invalide/);
  const nomBase=[...bases.keys()].find(n=>n.startsWith('pp-idb')&&n.includes('legacy'));
  const etat=bases.get(nomBase).get('active');const dir=[...dossiers.entries()].find(([n])=>n.startsWith('pp-opfs')&&n.includes('legacy'))[1];
  const ancien=JSON.parse(new TextDecoder().decode(dir.get(etat.file)));delete ancien.application;
  const contenu=new TextEncoder().encode(JSON.stringify(ancien));dir.set(etat.file,contenu);etat.hash=Buffer.from(await crypto.subtle.digest('SHA-256',contenu)).toString('hex');
  assert.equal(await lire(original,pp),'historique');await assert.rejects(etranger.load('v'));
});
test('blob altéré refusé avant ouverture et données inchangées non réécrites',async()=>{
  const s=creerStockage(chrs,'/corruption/');const args=await valeurs(chrs,'conservé');await s.save(...args,'v1');
  assert.equal((await s.save(...args,'v1')).changed,false);
  const etat=await s.load('v1');const entree=etat.files[chrs.base];
  const dir=[...dossiers.entries()].find(([n])=>n.includes('corruption'))[1];dir.set(entree.file,new Uint8Array([9]));
  await assert.rejects(etat.read(entree),/endommagé/);
});
test('inventaires incomplets ou incohérents refusés avant écriture',async()=>{
 const s=creerStockage(chrs,'/invalide/');const [inventory,read]=await valeurs(chrs,'base');
 await assert.rejects(s.save({...inventory,bytes:0},read,'v'),/Inventaire/);
 await assert.rejects(s.save({files:{...inventory.files,'media/../autre':inventory.files['secret-key']},bytes:1000},read,'v'),/Inventaire/);
 assert.equal(await s.load('v'),null);
});
test('état de secours annoncé uniquement après remplacement explicite',async()=>{
 const s=creerStockage(chrs,'/informations/');assert.deepEqual(await s.informations(),{present:false,version:null,secours:false});
 await s.save(...await valeurs(chrs,'initial'),'v1');assert.equal((await s.informations()).secours,false);
 await s.save(...await valeurs(chrs,'remplacement'),'v1','',true);
 assert.equal((await s.informations()).secours,true);assert.equal(await lire(s,chrs,true),'initial');
});

test('restauration explicite réécrit les blobs même si les empreintes du pointeur sont identiques',async()=>{
 const s=creerStockage(chrs,'/reparer/');const args=await valeurs(chrs,'intact');await s.save(...args,'v1');
 const etat=await s.load('v1');const entree=etat.files[chrs.base];
 const dir=[...dossiers.entries()].find(([n])=>n.includes('reparer'))[1];dir.set(entree.file,new Uint8Array([0]));
 await assert.rejects(etat.read(entree));
 await s.save(...args,'v1','',true,false,null,false);assert.equal(await lire(s,chrs),'intact');
 const db=bases.get([...bases.keys()].find(n=>n.includes('reparer')));const actif=db.get('active');dir.set(actif.file,new Uint8Array([0]));
 await assert.rejects(s.load('v1'));
 await s.save(...args,'v1','',true,false,null,false);assert.equal(await lire(s,chrs),'intact');
});
