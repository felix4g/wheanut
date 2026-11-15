const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const nodes=new Map();const node=()=>({value:'',innerHTML:'',textContent:'',dataset:{},classList:{add(){},remove(){},toggle(){}},addEventListener(){},setAttribute(){},querySelectorAll(){return []}});
const context={document:{querySelector(s){if(!nodes.has(s))nodes.set(s,node());return nodes.get(s)},querySelectorAll(){return []},addEventListener(){},dispatchEvent(){}},window:{},localStorage:{getItem(){return null},setItem(){}},setTimeout(){},clearTimeout(){},CustomEvent:class{},console};vm.createContext(context);vm.runInContext(fs.readFileSync('frontend/app.js','utf8'),context);
vm.runInContext(`
const checks=sample();
if(validateFields(checks).length!==6)throw Error('sample validation');
const pending={id:'test',name:'Test',prediction:'Pending',geometry:{type:'Polygon',coordinates:[rectangle(38.58,-121.82)]},dates:[],ndvi:[]};
if(validateFields([pending])[0].confidence!==null)throw Error('pending confidence');
if(!validRing(rectangle(38.58,-121.82)))throw Error('valid boundary rejected');
if(validRing([[0,0],[1,1],[0,1],[1,0],[0,0]]))throw Error('crossing boundary accepted');
for(const bad of [[checks[0],checks[0]],[{...checks[0],confidence:2}],[{...checks[0],ndvi:[4]}]]){let rejected=false;try{validateFields(bad)}catch{rejected=true}if(!rejected)throw Error('bad input accepted')}
window.Wheanut.applyResults([{id:'WH-001',prediction:'Grain',confidence:0.84}]);
if(window.Wheanut.getSelectedField().prediction!=='Grain')throw Error('agent result update failed');
const multi={...pending,id:'multi',geometry:{type:'MultiPolygon',coordinates:[[rectangle(38.58,-121.82)],[rectangle(38.60,-121.84)]]},season:2021,referenceLabel:'Silage',provenance:{sourceName:'Provided BARC'}};
if(validateFields([multi])[0].geometry.type!=='MultiPolygon')throw Error('MultiPolygon rejected');
if(Math.abs(area(multi)-2*area(pending))>1)throw Error('MultiPolygon area');
const roundTrip=validateFields([multi])[0];if(roundTrip.referenceLabel!=='Silage'||roundTrip.prediction!=='Pending'||roundTrip.provenance.sourceName!=='Provided BARC')throw Error('reference/provenance separation');
if(window.Wheanut.getGeoJSON().features.length!==6)throw Error('GeoJSON export failed');
`,context);console.log('PASS: sample and imported fields, crossing boundaries, duplicate IDs, invalid confidence/NDVI, Agent adapter and GeoJSON export');
