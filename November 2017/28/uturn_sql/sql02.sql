select feature_id,rfn.name,rfn.language_code,is_exonym from rdf_feature_name rfn, rdf_feature_names rfns where rfn.name_id=rfns.name_id and name_type='B' and rfn.name = 'Baruta' and is_exonym='N';


select feature_id,rfn.name,rfn.language_code from rdf_feature_name rfn, rdf_feature_names rfns where rfn.name_id=rfns.name_id and name_type='B' and rfns.feature_id = '23698581';

select feature_id,rfn.name,rfn.language_code from rdf_feature_name rfn, rdf_feature_names rfns where rfn.name_id=rfns.name_id and name_type='B' and rfns.feature_id =
(select country_id from rdf_admin_hierarchy where admin_place_id='23698581') and language_code in ('ENG','SPA') limit 1;

select count(distinct h.admin_place_id) from rdf_admin_hierarchy h where h.country_id=23355239


select feature_id,rfn.name,rfn.language_code,is_exonym ,admin_type,country_id,* from rdf_feature_name rfn, rdf_admin_hierarchy rah,rdf_feature_names rfns,rdf_admin_place rap 
where rap.admin_place_id=rfns.feature_id and rfn.name_id=rfns.name_id and name_type='B' and rfn.name = 'Bolívar' and is_exonym='N'
and admin_type=1119
and rah.admin_place_id=rfns.feature_id and country_id=23355239;