select h.admin_place_id,n.name as country from rdf_feature_name n, rdf_feature_names s, rdf_admin_hierarchy h 
where n.name_id=s.name_id and s.feature_id = h.country_id  and n.language_code='ENG' and name_type='B' and h.admin_place_id='21020836';

select distinct p.admin_place_id,p.admin_type,n.name from rdf_feature_name n, rdf_feature_names s,rdf_admin_place p
where n.name_id=s.name_id and s.feature_id=p.admin_place_id and s.feature_id='21020836';

# 根据ID 得到详细信息
select a.admin_place_id,a.admin_type,a.name,country
from 
(
 select distinct p.admin_place_id,p.admin_type,n.name from rdf_feature_name n, rdf_feature_names s,rdf_admin_place p
where n.name_id=s.name_id and s.feature_id=p.admin_place_id and s.feature_id='21020836'
) a
join 
(
 select h.admin_place_id,n.name as country from rdf_feature_name n, rdf_feature_names s, rdf_admin_hierarchy h 
where n.name_id=s.name_id and s.feature_id = h.country_id  and n.language_code='ENG' and name_type='B' and h.admin_place_id='21020836'
) b
on a.admin_place_id=b.admin_place_id


# 根据名称和order1_id得到 admin_place_id(feature_id)
 select feature_id from 
(select distinct feature_id from rdf_feature_name n, rdf_feature_names s where s.name_type='B' and n.name_id=s.name_id and n.name='Shelby' ) a
 join 
(select distinct admin_place_id from rdf_feature_names s,rdf_admin_hierarchy h where s.feature_id=h.admin_place_id and  h.order1_id in (select feature_id from rdf_feature_name n, rdf_feature_names s where s.name_type='B' and n.name_id=s.name_id and n.name='Tennessee' and n.language_code='ENG')) b
on a.feature_id = b.admin_place_id

#通过名称得到 order1_id
select s.feature_id,h.admin_place_id,n.name,h.order1_id,h.country_id,h.* from rdf_admin_hierarchy h,rdf_feature_names s,rdf_feature_name n
where s.name_id=n.name_id and h.admin_place_id=s.feature_id and s.name_type='B'  and n.name='Shelby'

select distinct h.order1_id from rdf_admin_hierarchy h,rdf_feature_names s,rdf_feature_name n where s.name_id=n.name_id and h.admin_place_id=s.feature_id and s.name_type='B' and n.language_code='ENG' and n.name='Shelby'

#通过名称 得到 order11_name
select distinct feature_id, n.name from rdf_feature_name n,rdf_feature_names s 
where n.name_id=s.name_id and s.name_type='B'  and s.feature_id in 
(
    select h.order1_id from rdf_admin_hierarchy h,rdf_feature_names s,rdf_feature_name n where s.name_id=n.name_id and h.admin_place_id=s.feature_id and s.name_type='B' and n.name='Shelby' and h.admin_place_id='21020836'
)

