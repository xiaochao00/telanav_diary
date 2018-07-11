use ElectricCommander;
my $ec = new ElectricCommander();

sub check_path{
	my $path = $_[0];
	-e $path || die "< $path> doesn't exist!";
}

# [1] check data path
my $new_data= "$[/myParent/p_pa_NewData]";
check_path($new_data);
check_path($new_data."/data");

my $baseline_data= "$[/myParent/p_pa_Baseline]";
check_path($baseline_data);
check_path($baseline_data."/data");

# [2] check compiler
my $compiler_path = "$[/myParent/p_pa_SnakeCatcherPath]";
-e $compiler_path || -e $compiler_path.".zip" || -e $compiler_path.".tar.gz" || die "Please check the input data path < ${compiler_path} >";


