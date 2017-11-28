#通过名称得到 order1_id
select s.feature_id,h.admin_place_id,n.name,h.order1_id,h.country_id,h.* from rdf_admin_hierarchy h,rdf_feature_names s,rdf_feature_name n
where s.name_id=n.name_id and h.admin_place_id=s.feature_id and s.name_type='B'  and n.name='Distrito Capital' and h.admin_order=1


select distinct feature_id, n.name country from rdf_feature_name n,rdf_feature_names s 
where n.name_id=s.name_id and s.name_type='B' and n.language_code='ENG'  and s.feature_id in 
(
    select distinct  h.order1_id from rdf_admin_hierarchy h,rdf_feature_names s,rdf_feature_name n 
    where s.name_id=n.name_id and h.admin_place_id=s.feature_id and s.name_type='B' and h.admin_place_id='23355164' and h.admin_order=1
)

#根据 admin_name 和 order1_name 得到 admin_place_id
select s.feature_id,* from rdf_feature_name n, rdf_feature_names s where s.name_type='B' and n.name_id=s.name_id and n.name='Distrito Capital'  
and feature_id in 
(
select distinct admin_place_id from rdf_feature_names s,rdf_admin_hierarchy h 
    where s.feature_id=h.admin_place_id and  h.admin_order=1 and h.order1_id in 
    (
        select distinct feature_id from rdf_feature_name n, rdf_feature_names s where s.name_type='B' and n.name_id=s.name_id and n.name='Distrito Capital'
    )
 )
 
 select * from rdf_admin_place where admin_place_id='23355228'
 select * from rdf_admin_hierarchy h where h.admin_place_id='23355228'
 
 
 
 select s.feature_id,* from rdf_feature_name n, rdf_feature_names s where s.name_type='B' and n.name_id=s.name_id and n.name='Distrito Capital'
 select * from rdf_admin_hierarchy where admin_place_id='23355164'

 
 