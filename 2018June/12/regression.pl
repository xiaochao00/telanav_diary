# [0]Execute
sub run_cmd{
    my $cmd = $_[0];
    print $cmd."\n";
    my $clout = `$cmd`;
    print $clout."\n";
    $? ne 0 && die $clout;
#    print $clout."\n";
}

my $local_workspace = "";
my $statistic_jar = "$[/myParent/p_pr_LocalStatisticPath]";
my $execute_path = "$[/myParent/p_pr_LocalExecutePath]";
my $vca_input = "$[/myParent/p_pr_LocalInput]"."/";
my $vca_base = "$[/myParent/p_pr_LocalBase]"."/";
my $target_region = lc("$[/myParent/p_pa_Region]");

# [1] statistic
print "1.1 statistic baseline data:";
run_cmd("java8 -jar ${statistic_jar} --d=${vca_base}");
print "1.2 statistic new data:";
run_cmd("java8 -jar ${statistic_jar} --d=${vca_input}");

# [2] generate test suits
print "2. generate test suits:";
run_cmd("cd ${execute_path};python testsuitesgenerator.py -r ${local_workspace} -d ${vca_base} -C 1 \n");

# [3] regression
print "3. regression";
run_cmd("cd ${execute_path};python vde_regression.py -N ${vca_input} -B ${vca_base} -R ${local_workspace}/report -r ${local_workspace}");
