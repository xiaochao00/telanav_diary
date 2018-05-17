import os
sql_time_cost_dict = {}
total_time_cost = 0
with open("adaptor all result.txt","r") as f:
    lines = f.readlines()
    sql_lines = []
    for line_index in range(len(lines)):
        line = lines[line_index]
        if not line or not line.strip().startswith("SELECT"):
            continue
        sql_line = line.strip()
        time_cost = lines[line_index+1].strip()
        total_time_cost += long(time_cost)
        sql_lines.append(line)
        sql_time_cost_dict.setdefault(line,[]).append(time_cost)

average_time_cost = float(total_time_cost*1.0/len(sql_lines))
print "total sql line number is ", len(sql_lines)
print "total distinct sql line number is ", len(sql_time_cost_dict)
print "average time cost is %.2f" % average_time_cost
for sql,time_list in sql_time_cost_dict.iteritems():
    if len(time_list)==1 and long(time_list[0])< average_time_cost:
        continue
    print sql
    print time_list
            
