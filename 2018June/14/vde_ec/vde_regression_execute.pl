#[0]Execute
sub run_cmd{
    my $cmd = $_[0];
    print $cmd."\n";
    my $clout = `$cmd`;
    $? ne 0 && die $clout;
    print $clout."\n";
}

my $local_workspace = "$[/myParent/p_pr_LocalWorkspace]";
my $regression_execute_path = "$[/myParent/p_pr_regressionExecutePath]";
my $statistic_execute_path = "$[/myParent/p_pr_statisticExecutePath]";


my $vde_input = "$[/myParent/p_pr_LocalInput]";
my $vde_baseline = "$[/myParent/p_pr_LocalBase]";
my $region_name = lc("$[/myParent/p_pa_Region]");
my $regression_report_path = "$[/myParent/p_pr_RegressionRepo]";

# [1] statistic
#run_cmd("cd ${local_workspace}");
run_cmd("cd ${local_workspace};java -Dfile.encoding=utf-8 -jar ${statistic_execute_path} --d=${vde_baseline}");
run_cmd("cd ${local_workspace};java -Dfile.encoding=utf-8 -jar ${statistic_execute_path} --d=${vde_input}");

# [2] generate test case
run_cmd("cd ${regression_execute_path};python testsuitesgenerator.py -r ${region_name} -d ${vde_baseline} -C 10");
# [3] execute regression
run_cmd("cd ${regression_execute_path};python vde_regression.py -N ${vde_input} -B ${vde_baseline} -R report -r ${region_name}");
#run_cmd("cd ${regression_execute_path};cp -r report/* ${regression_report_path};rm -rf report");")