select * from rdf_admin_place where admin_place_id = '21020836';
select feature_id,rfn.name,rfn.language_code from rdf_feature_name rfn, rdf_feature_names rfns where rfn.name_id=rfns.name_id and name_type='B' and rfns.feature_id = '21020836';

select * from rdf_admin_attribute where admin_place_id='21020836';

select * from rdf_feature_name where rdf_feature_name.name='Shelby' limit 10;


select feature_id,name_id from rdf_feature_name n, rdf_feature_names s where n.name_id=s.name_id and n.name='Shelby' and s.name_type='B' limit 10 ;
select feature_id,s.name_id,n.name from rdf_feature_name n, rdf_feature_names s where n.name_id=s.name_id and s.feature_id='21020362' and s.name_type='B' limit 10 ;

select * from rdf_admin_hierarchy h where h.admin_place_id in (select feature_id from rdf_feature_name n, rdf_feature_names s where n.name_id=s.name_id and n.name='Shelby' and s.name_type='B' limit 10);


select distinct feature_id,s.name_id,n.name,n.* from rdf_feature_name n, rdf_feature_names s where n.name_id=s.name_id and s.name_type='B' and s.feature_id in  
(select h.order1_id from rdf_admin_hierarchy h where h.admin_place_id in (select feature_id from rdf_feature_name n, rdf_feature_names s where n.name_id=s.name_id and n.name='Shelby' and s.name_type='B' ))
order by feature_id;

select * from rdf_feature_name n, rdf_feature_names s where s.name_type='B' and n.name_id=s.name_id and n.name='Shelby'  
and feature_id in 
(
select distinct admin_place_id from rdf_feature_names s,rdf_admin_hierarchy h where s.feature_id=h.admin_place_id and  h.order1_id in (select feature_id from rdf_feature_name n, rdf_feature_names s where s.name_type='B' and n.name_id=s.name_id and n.name='Tennessee' and n.language_code='ENG')
 )

select feature_id from 
(select distinct feature_id from rdf_feature_name n, rdf_feature_names s where s.name_type='B' and n.name_id=s.name_id and n.name='Shelby' ) a
 join 
(select distinct admin_place_id from rdf_feature_names s,rdf_admin_hierarchy h where s.feature_id=h.admin_place_id and  h.order1_id in (select feature_id from rdf_feature_name n, rdf_feature_names s where s.name_type='B' and n.name_id=s.name_id and n.name='Tennessee' and n.language_code='ENG')) b
on a.feature_id = b.admin_place_id
