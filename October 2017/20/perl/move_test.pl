use File::Copy;
use warnings;
use File::Copy::Recursive qw(fcopy rcopy dircopy fmove rmove dirmove);

my $from = 'C:\\Users\\shchshan\\Desktop\\files\\October 2017\\20\\perl\\a';
my $to = 'C:\\Users\\shchshan\\Desktop\\files\\October 2017\\20\\perl\\b';
dircopy($from,$to);