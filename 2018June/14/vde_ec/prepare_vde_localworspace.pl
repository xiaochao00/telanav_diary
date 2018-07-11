use File::Basename;
use IO::Handle qw( );
STDOUT->autoflush(1);
sub run_cmd{
	my $cmd = $_[0];
    print $cmd."\n";
    my $clout = `$cmd`;
    $? ne 0 && die $clout;
    print $clout."\n";
}

#[1] set local workspace
my $jobId = "$[/myJob/jobId]";
my $jobStepId = "$[/myJobStep/jobStepId]";
my $local_workspace = "$[/myProcedure/p_pr_LocalTempWorkDirectory]/".basename("$[/myParent/p_pa_NewData]")."_${jobId}_${jobStepId}";
print $local_workspace."\n";
-e $local_workspace||`mkdir -p $local_workspace`;
`ectool setProperty "/myParent/p_pr_LocalWorkspace"  $local_workspace`;

#[2] set tool
my $compiler_path = "$[/myParent/p_pa_SnakeCatcherPath]";
my $compiler_path_basename = basename($compiler_path);
if(-e $compiler_path){
`cp $[/myParent/p_pa_SnakeCatcherPath]/* $local_workspace`;
}elsif(-e "${compiler_path}.zip"){
	run_cmd("unzip ${compiler_path}.zip -d ${local_workspace}");
}else{
	die "Copy compiler exception! Please check <${compiler_path}>\n";
}
my $regression_execute_path = $local_workspace."/vde-regression";
my $statistic_execute_path = $local_workspace."/vde-statistic*.jar";

`ectool setProperty "/myParent/p_pr_regressionExecutePath" $regression_execute_path`;
`ectool setProperty "/myParent/p_pr_statisticExecutePath" $statistic_execute_path`;


#[3] set inputfile
my $local_workspace_input = "$local_workspace/"."input/data";
run_cmd("mkdir -p $local_workspace_input");
run_cmd("cp -r $[/myParent/p_pa_NewData]/data/* $local_workspace_input");
#run_cmd("cp -r $[/myParent/p_pa_NewData]/statistic ${local_workspace}/input");
`ectool setProperty "/myParent/p_pr_LocalInput" $local_workspace_input`;

#[4] set baseline
my $local_workspace_base = "$local_workspace/"."base/data";
run_cmd("mkdir -p $local_workspace_base");
run_cmd("cp -r $[/myParent/p_pa_Baseline]/data/* $local_workspace_base");
#run_cmd("cp -r $[/myParent/p_pa_Baseline]/statistic ${local_workspace}/base");
`ectool setProperty "/myParent/p_pr_LocalBase" $local_workspace_base`;
