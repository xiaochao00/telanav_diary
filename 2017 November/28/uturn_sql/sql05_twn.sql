select distinct n.name country from rdf_feature_name n,rdf_feature_names s 
where n.name_id=s.name_id and s.name_type='B' and n.language_code='ENG'  and s.feature_id in 
(
    select distinct h.order1_id from rdf_admin_hierarchy h,rdf_feature_names s,rdf_feature_name n 
    where s.name_id=n.name_id and h.admin_place_id=s.feature_id and s.name_type='B' and h.admin_place_id= '23525046' 
)

select * from rdf_admin_hierarchy h where h.admin_place_id='23525046'

select * from rdf_admin_place where admin_place_id='23525046'

select feature_id from rdf_feature_name rfn, rdf_feature_names rfns where rfn.name_id=rfns.name_id and name_type='B' and rfn.name = 'Taiwan' and language_code='ENG'

select a.admin_place_id,a.admin_type,a.name,country,language_code
from 
(
 select distinct p.admin_place_id,p.admin_type,n.name,language_code from rdf_feature_name n, rdf_feature_names s,rdf_admin_place p
where n.name_id=s.name_id and s.feature_id=p.admin_place_id and s.feature_id='23525046'
) a
join 
(
 select h.admin_place_id,n.name as country from rdf_feature_name n, rdf_feature_names s, rdf_admin_hierarchy h 
where n.name_id=s.name_id and s.feature_id = h.country_id  and n.language_code='ENG' and name_type='B' and h.admin_place_id='23525046'
) b
on a.admin_place_id=b.admin_place_id