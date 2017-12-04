use strict; 
use File::Find; 
use File::Copy;


my $path = 'C:\\Users\\shchshan\\Desktop\\files\\October 2017\\20\\perl'; 
my $search_file = "";
sub wanted { 
if ( -f $File::Find::name ) { 
 if ( $File::Find::name =~ /a.old$/) { 
  print "$File::Find::name\n"; 
  $search_file = "$File::Find::name";
  move("$File::Find::name","C:\\Users\\shchshan\\Desktop\\files\\October 2017\\20\\");
  }
 }
}
find( \&wanted, $path ); 
print "$search_file"