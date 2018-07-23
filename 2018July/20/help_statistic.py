# file_name = "speed_limit_diff_old_new.txt"
# file_name = "18q1_bridge_default_charge_diff.txt"
file_name = "18q1_charge_way_charge_diff.txt"
with open(file_name, "r") as f:
    
    old_id_list = set([])
    new_id_list = set([])
    for line in f:        
        if line and "+ " in line:
            new_id_list.add(line.split()[1])
        if line and "- " in line:
            old_id_list.add(line.split()[1])
    
    print "old count:", len(old_id_list)
    print "new count:", len(new_id_list)
    print "modified count:", len(new_id_list & old_id_list)
    
