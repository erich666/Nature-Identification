#!/usr/contrib/bin/perl
# Script to read flower, bird, whatever data and create web page and perl script init subroutine

$| = 1 ;	# turn off output buffering, so we see results if piped, etc
$[ = 1;		# set array base to 1

$pre = 'bird' ;
$pre = 'flwr' ;

# the one hard-coded thing - where the CGI script will be located
$cgiUrl = http://www.acm.org/tog/cgi/";

&PROCESS_ARGS() ;
&DOINIT() ;

&READDATA() ;

exit 0 ;

sub USAGE {
	print STDERR "usage: generic_pre.prl [prefix]\n" ;
	exit 1 ;
}

sub PROCESS_ARGS {
	local($arg) ;

	#if ( $#ARGV >= 1 ) {
	#	&USAGE() ;
	#}

	while(@ARGV) {
		$pre = shift(@ARGV) ;
		printf "file prefix is $pre\n";
	}
}

sub DOINIT {
	$input = $pre . "data.txt" ;
}

sub READDATA {
	unless (open(DATAFILE,$input)) {
		printf "Can't open $input: $!\n";
		exit 1 ;
	}
	&READCONTENTS() ;
	close(DATAFILE) ;
}

# read each line of the contents and store as an hotlink
sub READCONTENTS {

	$nf = 0 ;
	$nc = 0 ;
	$insection = '' ;
	while (<DATAFILE>) {
		chop;       # strip record separator
		@fld = split(' ',$_);
		if ( $#fld gt 0 && substr( $fld[1], 1, 1 ) ne '#' ) {	# skip blank and comment lines
			if ( substr( $fld[1], 1, 1 ) eq '!' ) {
				$insection = $fld[1] ;
			} elsif ( $insection eq '!data' ) {
				$obj[++$nf] = $_ ;
			} elsif ( $insection eq '!categories' ) {
				$category[++$nc] = $_ ;
			} elsif ( $insection eq '!name' ) {
				$singularTitle = $fld[1] ;
				$pluralTitle = $singularTitle . 's' ;
			} elsif ( $insection eq '!url' ) {
				$webUrl = $fld[1] ;
			} elsif ( $insection eq '!files' ) {
			 	$inputhmtltop = $fld[1] ;
				$inputhmtlbottom = $fld[2] ;
			 	$inputquizhmtltop = $fld[3] ;
				$inputquizhmtlbottom = $fld[4] ;
				$inputperltop = $fld[5] ;
				$outputhtml = $fld[6] ;
				$outputquizhtml = $fld[7] ;
				$outputperl = $fld[8] ;
			}
		}
	}

	# open output files
	unless (open(HTMLFILE, '>' . $outputhtml )) {
		printf "Can't open output html file $outputhtml: $!\n";
		exit 1 ;
	}
	unless (open(HTMLQUIZFILE, '>' . $outputquizhtml )) {
		printf "Can't open output quiz file $outputquizhtml: $!\n";
		exit 1 ;
	}

	# copy HTML header over
	unless (open(COPYFILE,$inputhmtltop)) {
		printf "Can't open input html top $inputhmtltop: $!\n";
		exit 1 ;
	}
	while (<COPYFILE>) { print HTMLFILE $_; }
	close(COPYFILE) ;

	# copy HTML QUIZ header over
	unless (open(COPYFILE,$inputquizhmtltop)) {
		printf "Can't open input quiz html top $inputquizhmtltop: $!\n";
		exit 1 ;
	}
	while (<COPYFILE>) { print HTMLQUIZFILE $_; }
	close(COPYFILE) ;

	printf HTMLFILE "<hr>/n<form action="$cgiUrl$outputperl" method="POST" name="flowerform">

	printf HTMLFILE "Check the characteristics that you see (you can always hit \"Back\" and change these later).\n";

	printf HTMLQUIZFILE "<form action=\"$cgiUrl\" method=\"POST\" name=\"%sform\">\n", $singularTitle;

        print HTMLQUIZFILE <<"(END HTML SECTION1)";
<P>
<INPUT type="submit" value="     Create a Quiz     " align="middle">
<P>
How many questions would you like to answer?<BR>
&nbsp;&nbsp;<SELECT NAME="quiz"> 
<OPTION>2 
<OPTION SELECTED>5 
<OPTION>10 
<OPTION>20 
<OPTION>50 
</SELECT>

<P>
You can choose the types of questions you want to answer:<BR>
&nbsp;&nbsp;<INPUT type="checkbox" name="qt" value="1" CHECKED> Yes/No questions<BR>
(END HTML SECTION1)

	$LCsingularTitle = lc($singularTitle);
	$LCpluralTitle = lc($pluralTitle);

	printf HTMLQUIZFILE "&nbsp;&nbsp;<INPUT type=\"checkbox\" name=\"qt\" value=\"2\" CHECKED> Which $LCsingularTitle has this characteristic?<BR>\n";
	printf HTMLQUIZFILE "&nbsp;&nbsp;<INPUT type=\"checkbox\" name=\"qt\" value=\"3\" CHECKED> Which characteristic does this $LCsingularTitle have?<BR>\n";
	printf HTMLQUIZFILE "&nbsp;&nbsp;<INPUT type=\"checkbox\" name=\"qt\" value=\"4\" CHECKED> For these two characteristics, which $LCsingularTitle has both?<BR>\n";
	printf HTMLQUIZFILE "&nbsp;&nbsp;<INPUT type=\"checkbox\" name=\"qt\" value=\"5\" CHECKED> For these two %ss, which characteristic is common to both?<BR>\n", $LCsingularTitle ;

	#select STDOUT ;	# unselect quiz file for output

	unless (open(PERLFILE, '>' . $outputperl )) {
		printf "Can't open output perl $outputperl: $!\n";
		exit 1 ;
	}

	# copy perl program over
	unless (open(COPYFILE,$inputperltop)) {
		printf "Can't open input perl top $inputperltop: $!\n";
		exit 1 ;
	}
	while (<COPYFILE>) { print PERLFILE $_; }
	close(COPYFILE) ;

	# post-process !names

	# post-process !categories
	printf PERLFILE "sub init {\n\n";

	printf PERLFILE "    \$objectUrl = \"$cgiUrl$outputperl\" ;\n\n";
	printf PERLFILE "    \$htmlUrl = \"$webUrl\" ;\n\n";
	printf PERLFILE "    \$idHtml = \"$outputhtml\" ;\n\n";
	printf PERLFILE "    \$quizHtml = \"$outputquizhtml\" ;\n\n";

	printf PERLFILE "    \$objectTitleCapsPlural = \"$pluralTitle\" ;\n";
	printf PERLFILE "    \$objectTitlePlural = lc(\$objectTitleCapsPlural);\n\n";

	printf PERLFILE "    \$objectTitleCaps = \$objectTitleCapsPlural ;\n";
	printf PERLFILE "    chop \$objectTitleCaps ;\n";
	printf PERLFILE "    \$objectTitle = lc(\$objectTitleCaps);\n\n";

	printf PERLFILE "    \$numChar = $nc ;\n\n" ;

	printf HTMLQUIZFILE "<P>\nYou can select which characteristics you wish to be quizzed on:<BR>\n";

	$catStartIndex = 1 ;
	$catnameprevious = '';
	for ( $i = 1 ; $i <= $nc ; $i++ ) {
		@fld = split(' ',$category[$i]);
		# find the prefix, category, and subcategory: $catpre, $catname, $catsub
		$catpre = $fld[1] ;	# easy
		$insub = 0 ;
		$catname = '' ;
		$catsub = '' ;
		for ( $j = 2 ; $j <= $#fld ; $j++ ) {
			if ( $insub == 0 ) {
				if ( $fld[$j] =~ /:/ ) {
					$insub = 1 ;
					$catname .= $fld[$j] ;
					chop $catname ;
				} else {
					$catname .= $fld[$j] . ' ' ;
				}
			} else {
				$catsub .= $fld[$j] . ' ' ;
			}
		}
		chop $catsub ;
		$catsub =~ s/'/\\'/g;	# quote apostrophe
		# may need & substitution? >>>>>
		printf PERLFILE "\$chTitle{\'$catpre\'} = \'$catsub\' ;\n";
		printf PERLFILE "\$chNum\{\'$catpre\'\} = $i ;\n";

		if ( $catname ne $catnameprevious ) {
			$quizcat .= sprintf "<i>$catname</i><BR>\n";
			$catnameArray[++$numCatName] = $catname ;
			printf HTMLFILE "\n<P>\n<B>$catname</B><BR>\n";
			if ( $catnameprevious ne '' ) {
				printf HTMLQUIZFILE "&nbsp;&nbsp;<INPUT type=\"checkbox\" name=\"c\" value=\"$catStartIndex-%d\" CHECKED>$catnameprevious<BR>\n",$i-1;
			}
			$catnameprevious = $catname ;
			$catStartIndex = $i ;
		}
		if ( $catpre =~ /,/ ) {
			$cattype = $`;
			$catval = $';
		}
		printf HTMLFILE "&nbsp;&nbsp;<INPUT type=\"checkbox\" name=\"$cattype\" value=\"$catval\"> $catsub<BR>\n";
		$quizcat .= sprintf "&nbsp;&nbsp;<INPUT type=\"checkbox\" name=\"g\" value=\"$i\"> $catsub<BR>\n";
	}
	printf HTMLQUIZFILE "&nbsp;&nbsp;<INPUT type=\"checkbox\" name=\"c\" value=\"$catStartIndex-$nc\" CHECKED>$catname<BR>\n" ;
        
	print HTMLQUIZFILE <<"(END HTML SECTION2)";
<P>
<INPUT type="submit" value="     Create a Quiz     " align="middle">
<P>
You can choose what types of $LCpluralTitle you would like to be quizzed on, as a group.
Checking a characteristic in a group means $LCpluralTitle in that group will be used for making questions.
If you check a number of characteristics in one group (e.g. $catnameArray[1]), $LCpluralTitle with either of those characteristics will
be part of the group (not just $LCpluralTitle with both characteristics). If you check characteristics in different
groups, the set of $LCpluralTitle for each separate group is found, then $LCpluralTitle that are common to all sets are used.
Technically, within a group it's
"characteristics OR char. OR char." and overall it's "group AND group AND group".
<P>
Yes, this all sounds confusing, but the idea is that you can choose to be tested on $LCpluralTitle that have in common
two or more specific sets of characteristics from different groups. For example, if this program were for house types,
there might be two groups, <i>Number of Stories</i> and <i>Exterior Wall Material</i>. You could pick the characteristic
"one-story" from the first group, and "stucco" and "brick" from the second, and the group of all houses used would then be
"one-story AND (either stucco OR brick)".
Try it out and see.
<P>
Check the characteristics below:
<BR>
(END HTML SECTION2)

	printf HTMLQUIZFILE $quizcat ;
        print HTMLQUIZFILE <<"(END HTML SECTION3)";
<P>
<INPUT type="submit" value="     Create a Quiz     " align="middle">
<P>
Finally, if you're really into tailoring, you can pick the $LCpluralTitle on which to be tested.
These will be added to any $LCpluralTitle selected using the characteristics above. 
Just check the ones you want:
<P>
(END HTML SECTION3)

	printf PERLFILE "\n    \$NumObjects = $nf ;\n\n" ;

	printf PERLFILE "    \@ObjectName = \(\n";
	for ( $i = 1 ; $i <= $nf ; $i++ ) {
		@fld = split(' ',$obj[$i]);
		# find the prefix, name, and data: $datapre, $dataname, $databinary
		$datapre= $fld[1] ;	# easy
		$databinary[$i] = $fld[$#fld] ;	# easy
		$insub = 0 ;
		$dataname = '';
		for ( $j = 2 ; $j < $#fld ; $j++ ) {
			$dataname .= $fld[$j] . ' ' ;
		}
		chop $dataname ;
		$dataname =~ s/'/\\'/g;	# quote apostrophe
		printf PERLFILE "\'%s\'", $dataname;
		if ( $i < $nf ) { printf PERLFILE "," } ;
		printf PERLFILE "\n" ;
		printf HTMLQUIZFILE "&nbsp;&nbsp;<INPUT type=\"checkbox\" name=\"o\" value=\"$i\">$dataname<BR>\n";
	}
	printf PERLFILE "\);\n\n" ;
	printf PERLFILE "\@ObjectData = \(\n" ;
	for ( $i = 1 ; $i <= $nf ; $i++ ) {
		printf PERLFILE "  \'$databinary[$i]\'";
		if ( $i < $nf ) { printf PERLFILE "," } ;
		printf PERLFILE "\n" ;
	}
	printf PERLFILE ");\n\n}\n" ;

        print HTMLFILE <<"(END HTML SECTION4)";
<P>
<INPUT type="submit" value="     Identify     " align="middle">

<P>
If you want to clear your choices, hit <input type="reset" name="mybutton" value="Reset">
(END HTML SECTION4)


        print HTMLQUIZFILE <<"(END HTML SECTION5)";
<P>
<INPUT type="submit" value="     Create a Quiz     " align="middle">

<P>
If you want to clear your choices, hit <input type="reset" name="mybutton" value="Reset">
</form>
(END HTML SECTION5)

	# copy HTML bottom over
	unless (open(COPYFILE,$inputhmtlbottom)) {
		printf "Can't open input html bottom $inputhmtlbottom: $!\n";
		exit 1 ;
	}
	while (<COPYFILE>) { print HTMLFILE $_; }
	close(COPYFILE) ;

	# copy HTML QUIZ bottom over
	unless (open(COPYFILE,$inputquizhmtlbottom )) {
		printf "Can't open input quiz html bottom $inputhmtlquizbottom: $!\n";
		exit 1 ;
	}
	while (<COPYFILE>) { print HTMLQUIZFILE $_; }
	close(COPYFILE) ;
}

sub by_rating { $nametot{$b} <=> $nametot{$a} ; }
