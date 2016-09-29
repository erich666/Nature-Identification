#!/usr/bin/perl

# This program may be freely redistributed and modified. It is not to be used for profit without the
# written permission of Eric Haines, erich@acm.org.
# Copyright (c) 2003, all rights reserved.

# History:
# v1.0, by Eric Haines, 4/26/2003
# v1.1, by Eric Haines, 3/22/2006 - minor cleanup, added photo links immediately

# This is the top half of the generic database program.
# You want to run generic_db.pl to create the various databases.

$[ = 1;		# set array base to 1

$vsplitter = 'x' ;	# character that splits multiple values in token/value

@referers = ('www.realtimerendering.com','realtimerendering.com','www.acm.org');

# set data types
&init;

# Check Referring URL
&check_url;

# Parse Form Contents
&parse_form;

# Return HTML Page or Redirect User
&return_html;

sub check_url {

    # Localize the check_referer flag which determines if user is valid.     #
    local($check_referer) = 0;

    # If a referring URL was specified, for each valid referer, make sure    #
    # that a valid referring URL was passed to FormMail.                     #

    if ($ENV{'HTTP_REFERER'}) {
        foreach $referer (@referers) {
            if ($ENV{'HTTP_REFERER'} =~ m|https?://([^/]*)$referer|i) {
                $check_referer = 1;
                last;
            }
        }
    }
    else {
        $check_referer = 1;
    }

    # If the HTTP_REFERER was invalid, send back an error.                   #
    if ($check_referer != 1) { &error('bad_referer') }
}

sub parse_form {

    # Define the configuration associative array.                            #
    %Config = ('recipient','',          'subject','',
               'email','',              'realname','',
               'redirect','',           'bgcolor','',
               'background','',         'link_color','',
               'vlink_color','',        'text_color','',
               'alink_color','',        'title','',
               'sort','',               'print_config','',
               'required','',           'env_report','',
               'return_link_title','',  'return_link_url','',
               'print_blank_fields','', 'missing_fields_redirect','');

    # Determine the form's REQUEST_METHOD (GET or POST) and split the form   #
    # fields up into their name-value pairs.  If the REQUEST_METHOD was      #
    # not GET or POST, send an error.                                        #
    if ($ENV{'REQUEST_METHOD'} eq 'GET') {
        # Split the name-value pairs
        @pairs = split(/&/, $ENV{'QUERY_STRING'});
    }
    elsif ($ENV{'REQUEST_METHOD'} eq 'POST') {
        # Get the input
        read(STDIN, $buffer, $ENV{'CONTENT_LENGTH'});
 
        # Split the name-value pairs
        @pairs = split(/&/, $buffer);
    }
    else {
	#@pairs = ( 'quiz=5' ) ;
	#@pairs = ( 'quiz=5','c=8-11' ) ;
	#@pairs = ( 'quiz=5','qt=5','qt=2' ) ;
	#@pairs = ('qans=5','u1=2','f1=5x44x30x532x44','u2=1','f2=3x6x39x269','u3=2','f3=4x17x3x127x319','u4=2','f4=1x44x492','u5=2','f5=2x13x35x261','qval=11222') ;
	#@pairs = ('qans=5','u1=2','f1=5,44,30,532,44','u2=1','f2=3,6,39,269','u3=2','f3=4,17,3,127,319','u4=2','f4=1,44,492','u5=2','f5=2,13,35,261','qval=11222') ;

        &error('request_method');
    }

    # For each name-value pair:                                              #
    foreach $pair (@pairs) {

        # Split the pair up into individual variables.                       #
        local($name, $value) = split(/=/, $pair);
 
        # Decode the form encoding on the name and value variables.          #
        $name =~ tr/+/ /;
        $name =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;

        $value =~ tr/+/ /;
        $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;

        # If they try to include server side includes, erase them, so they
        # aren't a security risk if the html gets returned.  Another 
        # security hole plugged up.
        $value =~ s/<!--(.|\n)*-->//g;

        # If the field name has been specified in the %Config array, it will #
        # return a 1 for defined($Config{$name}}) and we should associate    #
        # this value with the appropriate configuration variable.  If this   #
        # is not a configuration form field, put it into the associative     #
        # array %Form, appending the value with a ', ' if there is already a #
        # value present.  We also save the order of the form fields in the   #
        # @Field_Order array so we can use this order for the generic sort.  #
        if (defined($Config{$name})) {
            $Config{$name} = $value;
        }
        else {
            if ($Form{$name} && $value) {
                $Form{$name} = "$Form{$name}, $value";
            }
            else {
                push(@Field_Order,$name);
                $Form{$name} = $value;
            }
        }
    }

    # The next six lines remove any extra spaces or new lines from the       #
    # configuration variables, which may have been caused if your editor     #
    # wraps lines after a certain length or if you used spaces between field #
    # names or environment variables.                                        #
    $Config{'required'} =~ s/(\s+|\n)?,(\s+|\n)?/,/g;
    $Config{'required'} =~ s/(\s+)?\n+(\s+)?//g;
    $Config{'env_report'} =~ s/(\s+|\n)?,(\s+|\n)?/,/g;
    $Config{'env_report'} =~ s/(\s+)?\n+(\s+)?//g;
    $Config{'print_config'} =~ s/(\s+|\n)?,(\s+|\n)?/,/g;
    $Config{'print_config'} =~ s/(\s+)?\n+(\s+)?//g;

    # Split the configuration variables into individual field names.         #
    @Required = split(/,/,$Config{'required'});
    @Env_Report = split(/,/,$Config{'env_report'});
    @Print_Config = split(/,/,$Config{'print_config'});
}

sub identify_header {
    # Print HTTP header and opening HTML tags.                           #
    print "Content-type: text/html\n\n";
    print "<html>\n <head>\n";

    # Print out title of page                                            #
    if ($Config{'title'}) { print "  <title>$Config{'title'}</title>\n" }
    else                  { print "  <title>$objectTitleCapsPlural Identified</title>\n" }

    print " </head>\n <body";

    # Get Body Tag Attributes                                            #
    &body_attributes;

	# Close Body Tag                                                     #
    print ">\n";

    # Print custom or generic title.                                     #
    if ($Config{'title'}) { print "   <h1>$Config{'title'}</h1>\n" }
    else { print "   <h1>$objectTitleCapsPlural Identified</h1>\n" }

    print "<b>Hint:</b> from this page, use your middle or right mouse button when clicking on the links to open a new tab for each result.\n";
	printf "<P>\n" ;
}

sub identify_header_object {
	my $oname;
   	($oname) = @_;

        # Print HTTP header and opening HTML tags.                           #
        print "Content-type: text/html\n\n";
        print "<html>\n <head>\n";

        # Print out title of page                                            #
        if ($Config{'title'}) { print "  <title>$Config{'title'}: $oname</title>\n" }
        else                  { print "  <title>$objectTitleCapsPlural Identified: $oname</title>\n"        }

        print " </head>\n <body";

        # Get Body Tag Attributes                                            #
        &body_attributes;

        # Close Body Tag                                                     #
        print ">\n";

        # Print custom or generic title.                                     #
        if ($Config{'title'}) { print "   <h1>$Config{'title'}: $oname</h1>\n" }
        else { print "   <h1>$objectTitleCapsPlural Identified: $oname</h1>\n" }

        print "\n";
	printf "<BR>\n" ;
}

sub return_html {
    # Local variables used in this subroutine initialized.                   #
    local($key,$sort_order,$sorted_field);

    # If redirect option is used, print the redirectional location header.   #
    if ($Config{'redirect'}) {
        print "Location: $Config{'redirect'}\n\n";
    }

    # Otherwise, begin printing the response page.                           #
    else {

 
	&identify;

        # Print the page footer.                                             #
        print <<"(END HTML FOOTER)";
<hr>
<I><a href="http://www.erichaines.com/">Eric Haines</a>,
<a href="mailto:erich\@acm.org">erich\@acm.org</a></I>
</body>
</html>
(END HTML FOOTER)
    }
}

sub body_attributes {
    # Check for Background Color
    if ($Config{'bgcolor'}) { print " bgcolor=\"$Config{'bgcolor'}\"" }

    # Check for Background Image
    if ($Config{'background'}) { print " background=\"$Config{'background'}\"" }

    # Check for Link Color
    if ($Config{'link_color'}) { print " link=\"$Config{'link_color'}\"" }

    # Check for Visited Link Color
    if ($Config{'vlink_color'}) { print " vlink=\"$Config{'vlink_color'}\"" }

    # Check for Active Link Color
    if ($Config{'alink_color'}) { print " alink=\"$Config{'alink_color'}\"" }

    # Check for Body Text Color
    if ($Config{'text_color'}) { print " text=\"$Config{'text_color'}\"" }
}

sub error { 
    # Localize variables and assign subroutine input.                        #
    local($error,@error_fields) = @_;
    local($host,$missing_field,$missing_field_list);

    if ($error eq 'bad_referer') {
        if ($ENV{'HTTP_REFERER'} =~ m|^https?://([\w\.]+)|i) {
            $host = $1;
            print <<"(END ERROR HTML)";
Content-type: text/html

<html>
 <head>
  <title>Bad Referrer - Access Denied</title>
 </head>
 <body bgcolor=#FFFFFF text=#000000>
  <center>
   <table border=0 width=600 bgcolor=#9C9C9C>
    <tr><th><font size=+2>Bad Referrer - Access Denied</font></th></tr>
   </table>
   <table border=0 width=600 bgcolor=#CFCFCF>
    <tr><td>The form attempting to use
     <a href="http://www.worldwidemart.com/scripts/formmail.shtml">FormMail</a>
     resides at <tt>$ENV{'HTTP_REFERER'}</tt>, which is not allowed to access
     this cgi script.<p>

     If you are attempting to configure FormMail to run with this form, you need
     to add the following to \@referers, explained in detail in the README file.<p>

     Add <tt>'$host'</tt> to your <tt><b>\@referers</b></tt> array.<hr size=1>
     <center><font size=-1>
      <a href="http://www.worldwidemart.com/scripts/formmail.shtml">FormMail</a> V1.6 &copy; 1995 - 1997  Matt Wright<br>
      A Free Product of <a href="http://www.worldwidemart.com/scripts/">Matt's Script Archive, Inc.</a>
     </font></center>
    </td></tr>
   </table>
  </center>
 </body>
</html>
(END ERROR HTML)
        }
        else {
            print <<"(END ERROR HTML)";
Content-type: text/html

<html>
 <head>
  <title>FormMail v1.6</title>
 </head>
 <body bgcolor=#FFFFFF text=#000000>
  <center>
   <table border=0 width=600 bgcolor=#9C9C9C>
    <tr><th><font size=+2>FormMail</font></th></tr>
   </table>
   <table border=0 width=600 bgcolor=#CFCFCF>
    <tr><th><tt><font size=+1>Copyright 1995 - 1997 Matt Wright<br>
        Version 1.6 - Released May 02, 1997<br>
        A Free Product of <a href="http://www.worldwidemart.com/scripts/">Matt's Script Archive,
        Inc.</a></font></tt></th></tr>
   </table>
  </center>
 </body>
</html>
(END ERROR HTML)
        }
    }

    elsif ($error eq 'request_method') {
            print <<"(END ERROR HTML)";
Content-type: text/html

<html>
 <head>
  <title>Error: Request Method</title>
 </head>
 <body bgcolor=#FFFFFF text=#000000>
  <center>
   <table border=0 width=600 bgcolor=#9C9C9C>
    <tr><th><font size=+2>Error: Request Method</font></th></tr>
   </table>
   <table border=0 width=600 bgcolor=#CFCFCF>
    <tr><td>The Request Method of the Form you submitted did not match
     either <tt>GET</tt> or <tt>POST</tt>.  Please check the form and make sure the
     <tt>method=</tt> statement is in upper case and matches <tt>GET</tt> or <tt>POST</tt>.<p>

     <center><font size=-1>
      <a href="http://www.worldwidemart.com/scripts/formmail.shtml">FormMail</a> V1.6 &copy; 1995 - 1997  Matt Wright<br>
      A Free Product of <a href="http://www.worldwidemart.com/scripts/">Matt's Script Archive, Inc.</a>
     </font></center>
    </td></tr>
   </table>
  </center>
 </body>
</html>
(END ERROR HTML)
    }
    exit;
}

sub list_object {

	# print HTML header
	&identify_header_object($ObjectName[$objectListNum]); 

	$fnameplus = $ObjectName[$objectListNum] ;
	$fnameplus =~ s/ /+/g ;
	if ( $fnameplus =~ m/\// ) {	# search for "/"
		$fnameplus = $` ;	# trim all before "/"
	}
	if ( $fnameplus =~ m/\+&/ ) {	# search for +&
		$fnameplus = $' ;	# remove everything before it
	}
	#$fnameplus .= "+$objectTitle";
	$fnameplus = "'" . $fnameplus . "' bird";	# quotes around it works better yet
	printf "<P>You can <a href=\"http://images.google.com/images?q=$fnameplus\">search Google Images</a> for images of this $objectTitle.\n<P>\n";
        
	# make list of characteristics by array location
	foreach $cc (keys %chNum) {
		$chArray[$chNum{$cc}] = $chTitle{$cc} ;
	}
	my $hashave = 'has';
	if ( $ObjectName[$objectListNum] =~ / & / ) {
		$hashave = 'have';
	}
	printf "<B>$ObjectName[$objectListNum]</B> $hashave these characteristics:<BR><UL>\n";
	$fchar = $ObjectData[$objectListNum] ;
	for ( $ic = 1 ; $ic <= $numChar ; $ic++ ) {
		if ( substr($fchar,$ic,1) eq '+' ) {
			printf "<LI> $chArray[$ic]<BR>\n" ;
		}
	}
	printf "</UL>\n";

	print <<"(END HTML START)";

<P>
Use your browser's Back button if you want to change anything and try again.
(END HTML START)
}

sub identify {

	# $f is token, $Form{$f} is value string
	foreach $f (keys %Form) {
		@flist = split(', ',$Form{$f}) ;

		# special page: if 'object' is in list, list characteristics of object in a separate web page
		if ( $f eq 'object' ) {
			$objectListNum = $Form{$f} ;
			&list_object;
			return ;
		}
		
		# special page: if 'quiz' is in list, generate a quiz
		if ( $f eq 'quiz' ) {
			&make_quiz;
			return ;
		}
		
		# special page: if 'qans' is in list, score a quiz
		if ( $f eq 'qans' ) {
			&grade_quiz;
			return ;
		}
		
		for ( $ii = 1 ; $ii <= $#flist ; $ii++ ) {
			$elem = $f . ',' . $flist[$ii] ;
			$findList[++$fln] = $chNum{$elem} ;
			$chArray{$chNum{$elem}} = $chTitle{$elem} ;
		}
	}
	# print HTML header
	&identify_header; 
	if ( $fln > 0 ) {
		printf "<font size=\"+1\">For these characteristics:</font>\n<UL>\n" ;
  		for ( $ii = 1 ; $ii <= $numChar ; $ii++ ) {
  			if ( exists($chArray{$ii}) ) {
  				printf "<LI>$chArray{$ii}\n" ;
			}
		}
		printf "</UL>\n<P><font size=\"+1\">The following $objectTitlePlural match:</font><P>" ;
	} else {
		printf "<font size=\"+1\">No $objectTitle characteristics chosen; all $objectTitlePlural follow.</font><P>\n" ;
	}

	# go through each object, see if it's a match
	$got_one = 0 ;
	for ( $if = 1 ; $if <= $NumObjects ; $if++ ) {
		$fchar = $ObjectData[$if] ;
		$good = 1 ;
		for ( $ic = 1 ; $ic <= $fln && $good ; $ic++ ) {
			if ( substr($fchar,$findList[$ic],1) ne '+' ) {
				$good = 0 ;
			}
		}
		if ( $good ) {
			$got_one = 1 ;
			my $fnameplus = $ObjectName[$if] ;
			$fnameplus =~ s/ /+/g ;		# change spaces to +
			if ( $fnameplus =~ m/\// ) {	# search for "/"
				$fnameplus = $` ;	# trim all before "/"
			}
			if ( $fnameplus =~ m/\+&\+/ ) {	# search for +&
				$fnameplus = $' ;	# remove everything before it
			}
			if ( $fnameplus =~ m/\+or\+/ ) {	# search for ' or '
				$fnameplus = $' ;	# remove everything before it
			}
			$fnameplus = "'" . $fnameplus . "' bird";	# quotes around it works better yet
			printf ( "&nbsp;&nbsp;<a href=\"$objectUrl?object=$if\">$ObjectName[$if]</a> (<a href=\"http://images.google.com/images?q=$fnameplus\">photos</a>)<BR>\n" ) ;
		}
	}
	if ( $got_one == 0 ) {
		printf "No $objectTitlePlural found. If you select a characteristic and the $objectTitle does not have it,\n";
		printf "the $objectTitle is eliminated from the list. So, if you are not sure if a $objectTitle has a\n";
		printf "characteristic, do not select it.<P>\n" ;
	}

        print <<"(END HTML START)";

<P>
Use your browser's Back button if you want to change anything and try again.
(END HTML START)
}

#################################################


# quiz token/value pairs
#    example: quiz=5
# quiz=# - number of questions
#
# There are currently 6 types of questions. This can be trimmed down by:
# qt=1,2,3,5 - limit to question types 1,2,3,5
#
# There are also ways to trim down the number of objects that are to be tested on:
# o=#,#,#-# - objects to be quizzed on (default is all), ex. o=1,5,9-20,23,29,43-201
#   (If combined with "oc" below, these birds are forced to be used, i.e. ORed in)
# g=#,#,# - characteristic group list: any obj with any of these characteristics is OK.
#   If there are multiple "oc" listings, the new "oc" object list is made and then
#   ANDed (not ORed) with the summary list.
# And you can determine which characteristics are used in questions:
# c=#,#,... - characteristics which are to be used to generate questions (default is all)
#
sub make_quiz {
	# make list of characteristics by array location
	foreach $cc (keys %chNum) {
		$chArray[$chNum{$cc}] = $chTitle{$cc} ;
		$chGroup[$chNum{$cc}] = $cc ;
	}

	# initialize stuff
	$maxQuestionTypes = 5 ;
 	for ( $ii = 1 ; $ii <= $maxQuestionTypes ; $ii++ ) {
 		$questionType[$ii] = 0 ;
 	}

	# $f is token, $Form{$f} is value string
	foreach $f (keys %Form) {
		@flist = split(', ',$Form{$f}) ;

		# quiz page answers here
		if ( $f eq 'quiz' ) {
			$numQuiz = $Form{$f};
		}
		
		# quiz questions to use
		if ( $f eq 'qt' ) {
			for ( $iii = 1 ; $iii <= $#flist ; $iii++ ) {
				$questionType[$flist[$iii]] = 1;
			}
		}

		# characteristics to use
		if ( $f eq 'c' ) {
			$charSelectionFlag = 1;
			$charTimesCalled += $#flist ;
			for ( $iii = 1 ; $iii <= $#flist ; $iii++ ) {
				if ( $flist[$iii] =~ /-/ ) {
					$ibeg = $` ;
					$iend = $' ;
					for ( $ik = $ibeg ; $ik <= $iend ; $ik++ ) {
						$charSelBit[$ik] = 1;
					}
				} else {
					$charSelBit[$flist[$iii]] = 1;
				}
			}
		}

		# objects to use
		if ( $f eq 'o' ) {
			$objSelectionFlag = 1;
			for ( $iii = 1 ; $iii <= $#flist ; $iii++ ) {
				if ( $flist[$iii] =~ /-/ ) {
					$ibeg = $` ;
					$iend = $' ;
					for ( $ik = $ibeg ; $ik <= $iend ; $ik++ ) {
						$objSingleSelBit[$ik] = 1;
					}
				} else {
					$objSingleSelBit[$flist[$iii]] = 1;
				}
			}
		}

		# filtered objects to use
		if ( $f eq 'g' ) {
			$groupSelectionFlag = 1;
			for ( $iii = 1 ; $iii <= $#flist ; $iii++ ) {
				if ( $flist[$iii] =~ /-/ ) {
					$ibeg = $` ;
					$iend = $' ;
					for ( $ik = $ibeg ; $ik <= $iend ; $ik++ ) {
						$groupSelBit[$ik] = 1;
					}
				} else {
					$groupSelBit[$flist[$iii]] = 1;
				}
			}
		}
	}

	$numCharSelSet = 0 ;
	if ( $charSelectionFlag == 1 ) {
		# initialize charSelSet, the set of characteristics in use; value saved is real char
		for ( $ii = 1 ; $ii <= $numChar ; $ii++ ) {
			if ( $charSelBit[$ii] == 1 ) {
				$charSelSet[++$numCharSelSet] = $ii ;
			}
		}
	} else {
		# set charSelSet to identity (does nothing) - all characteristics are used
		for ( $ii = 1 ; $ii <= $numChar ; $ii++ ) {
			$charSelSet[++$numCharSelSet] = $ii ;
		}
	}

	# select among objects
	if ( $groupSelectionFlag ) {
		for ( $ik = 1 ; $ik <= $NumObjects ; $ik++ ) {
			$groupObjBit[$ik] = 0 ;
			$objSelBit[$ik] = 1 ;
		}
		$prevGroup = '' ;
		# or or or AND or or or AND or or or
		for ( $ii = 1 ; $ii <= $numChar ; $ii++ ) {
			if ( $groupSelBit[$ii] == 1 ) {
				# is this a new group?
		 		if ( $chGroup[$ii] =~ /,/ ) {
					$curGroup = $`;
					#$chval = $';
				}
				if ( $prevGroup ne '' && $prevGroup ne $curGroup ) {
					# new group, so AND in previous results to total, if any
					for ( $ik = 1 ; $ik <= $NumObjects ; $ik++ ) {
						$objSelBit[$ik] = $objSelBit[$ik] & $groupObjBit[$ik] ;
						$groupObjBit[$ik] = 0 ;	# and clear for new set
					}
				}
				$prevGroup = $curGroup ;
				# mark all objects that have this bit set
				for ( $ik = 1 ; $ik <= $NumObjects ; $ik++ ) {
					if ( substr($ObjectData[$ik],$ii,1) eq '+' ) {
						$groupObjBit[$ik] = 1 ;
					}
				}
			}
		}
		# merge final group
		for ( $ik = 1 ; $ik <= $NumObjects ; $ik++ ) {
			$objSelBit[$ik] = $objSelBit[$ik] & $groupObjBit[$ik] ;
		}
	}
	# add in any individual objects selected
	if ( $objSelectionFlag == 1 ) {
		for ( $ik = 1 ; $ik <= $NumObjects ; $ik++ ) {
			if ( $objSingleSelBit[$ik] == 1 ) {
				$objSelBit[$ik] = 1 ;
			}
		}
	} elsif ( $groupSelectionFlag != 1 ) {
		# no special object selection, select all
		for ( $ik = 1 ; $ik <= $NumObjects ; $ik++ ) {
			$objSelBit[$ik] = 1 ;
		}
	}
	# objSelBits are all set at this point, translate to objSelSet.
	$numObjSelSet = 0 ;
	for ( $ii = 1 ; $ii <= $NumObjects ; $ii++ ) {
		if ( $objSelBit[$ii] == 1 ) {
			$objSelSet[++$numObjSelSet] = $ii ;
		}
	}

	# wait until now to print, as number of quiz questions is passed in
	&quiz_questions_header;

	if ( $numCharSelSet <= 2 ) {
		&not_enough_characteristics;
		$quizFailed = 1 ;
		goto QuizEnd;
	}
	if ( $numQuiz < 1 || $numQuiz > 100 ) {
		printf "<P>Number of quiz questions is limited to between 1 and 100 - please report this error to <a href=\"mailto:erich\@acm.org\">erich\@acm.org</a>\n";
		$quizFailed = 1 ;
		goto QuizEnd;
	}
	if ( $numObjSelSet < 2 ) {
		printf "<P>You need to have more than two $objectTitlePlural in order to generate a quiz. Please click the \"Back\" button and try again.\n";
		$quizFailed = 1 ;
		goto QuizEnd;
	}

	printf "<P>\n<form action=\"$objectUrl\" method=\"get\" name=\"quiz$objectTitle\">\n" ;
	printf "<INPUT TYPE=\"hidden\" NAME=\"qans\" VALUE=\"$numQuiz\">\n";
	printf "<OL>\n";

	# make the quiz
	# - Generate a random quiz question
	# - Store away the question and answer string to pass to script
	
	# First, which question types are available?
	# if there is only one characteristic type picked, it's sorta stupid to have "both characteristics" questions
	$numQuestionTypes = 0 ;
	for ( $ii = 1 ; $ii <= $maxQuestionTypes ; $ii++ ) {
		if ( $questionType[$ii] != 0 && &valid_question($ii,$charTimesCalled) ) {
			$questionTypeIndex[++$numQuestionTypes] = $ii ;
		}
	}
	if ( $numQuestionTypes < 1 ) {
		# no questions are valid (ha!), so set all questions valid
		$numQuestionTypes = 0 ;
		for ( $ii = 1 ; $ii <= $maxQuestionTypes ; $ii++ ) {
			# adjust if only one characteristic is chosen (get rid of last three question types if only one char set)
			if ( &valid_question($ii,$charTimesCalled) ) {
 				#$questionType[$ii] = 1 ;
				$questionTypeIndex[++$numQuestionTypes] = $ii ;
			}
		}
	}

	for ( $qq = 1 ; $qq <= $numQuiz ; $qq++ ) {
		$tryTimes = 0 ;
		do {
			$char1 = $char2 = $obj1 = $obj2 = '' ;	# cleared for hashing
			$currQuestion = $questionTypeIndex[int(1+rand($numQuestionTypes))];
			if ( $currQuestion == 1 ) { $worked = &create_question_type1; }
			elsif ( $currQuestion == 2 ) { $worked = &create_question_type2; }
			elsif ( $currQuestion == 3 ) { $worked = &create_question_type3; }
			elsif ( $currQuestion == 4 ) { $worked = &create_question_type4; }
			else { $worked = &create_question_type5; }
		} while ( $worked == 0 && $tryTimes++ < 20 ) ;
		if ( $worked == 0 ) {
			printf "</OL>\n<P>Sorry, it appears that you have chosen a set of characteristics\n";
			printf "and $objectTitlePlural that makes it extremely difficult to create enough questions.\n";
			printf "Quitting: please click your browser's \"Back\" button and try again.\n";
			$quizFailed = 1 ;
			goto QuizEnd;
		}
	}
	printf "</OL>\n";

	QuizEnd:
	&quiz_questions_footer ;
}
# first argument is question #, second argument is 1 if we should throw away all questions with two characteristics
sub valid_question {
	my $qtype ;
	my $qthrow ;
   	($qtype,$qthrow) = @_;
	if ( $qthrow == 1 ) {
		if ( $qtype >= 3 ) {
			return 0 ;
		}
	}
	return 1 ;
}

sub not_enough_characteristics {
	printf "<P>There are not enough characteristics chosen to make reasonable questions. Please click the \"Back\" button and try again.\n";
}

sub print_question_type1 {
	if ( $hyperlinkObject != 0 ) {
		$obj1name = "<a href=\"" . $objectUrl . "?object=" . $obj1 . "\">" . $ObjectName[$obj1] . "</a>" ;
	} else {
		$obj1name = $ObjectName[$obj1] ;
	}

	$ana = &starts_with_vowel($obj1name) ? "an" : "a" ;
	printf "<LI>Does $ana <b>$obj1name</b> have this characteristic: <i>$chArray[$char1]</i>?<BR>\n";
}
sub create_question_type1 {

	# select right answer only once, we don't want to bias results.
	$lookFor = int(rand(2)+1);	# 1 or 2
	$countQuest = 0 ;
	do {
		$obj1 = &select_random_object() ;
		$char1 = &select_random_char() ;
		$answerval = ( substr($ObjectData[$obj1],$char1,1) eq '+' ) ? '1' : '2' ;
		$questionHash = &make_question_hash('1');
	# assumes $obj1 has some char1 that is true and some that is false; watch out if we subset.
	} while ( ($countQuest++ < 20) && ($answerval != $lookFor || exists($questionsAsked{$questionHash})) ) ;
	if ( $countQuest >= 20 ) { return 0 ; }
	$questionsAsked{$questionHash} = 1 ;

	&print_question_type1 ;
	printf "&nbsp;&nbsp;<INPUT type=\"radio\" name=\"u$qq\" value=\"1\"> A. Yes<BR>\n";
	printf "&nbsp;&nbsp;<INPUT type=\"radio\" name=\"u$qq\" value=\"2\"> B. No<BR>\n<P>\n";
	printf "<INPUT TYPE=\"hidden\" NAME=\"f$qq\" VALUE=\"1$vsplitter$char1$vsplitter$obj1\">\n";

	# append answer string
	$qansval .= $answerval ;
	return 1 ;
}
# Which wildflower has this characteristic?
sub print_question_type2 {
	printf "<LI>Which $objectTitle has this characteristic: <i>$chArray[$char1]</i>?<BR>\n";
}
sub create_question_type2 {

	$countQuest = 0 ;
	do {
		$char1 = &select_random_char() ;
		$obj1 = &select_random_object_with_char($char1,'+') ;
		$obj2 = &select_random_object_with_char($char1,'.') ;
		$questionHash = &make_question_hash('2');
	} while ( ($countQuest++ < 20) &&
		  ( $obj1 == 0 || $obj2 == 0 || exists($questionsAsked{$questionHash}) ) ) ;
	if ( $countQuest >= 20 ) { return 0 ; }
	$questionsAsked{$questionHash} = 1 ;

	if ( rand(2) >= 1 ) {
		$answerval = 2 ;
		# swap
		$temp = $obj1 ; $obj1 = $obj2 ; $obj2 = $temp ;
	} else {
		$answerval = 1 ;
	}
	&print_question_type2 ;
	printf "&nbsp;&nbsp;<INPUT type=\"radio\" name=\"u$qq\" value=\"1\"> A. <b>$ObjectName[$obj1]</b><BR>\n";
	printf "&nbsp;&nbsp;<INPUT type=\"radio\" name=\"u$qq\" value=\"2\"> B. <b>$ObjectName[$obj2]</b><BR>\n<P>\n";
	printf "<INPUT TYPE=\"hidden\" NAME=\"f$qq\" VALUE=\"2$vsplitter$char1$vsplitter$obj1$vsplitter$obj2\">\n";

	# append answer string
	$qansval .= $answerval ;
	return 1 ;
}

# Which characteristic does this wildflower have?
sub print_question_type3 {
	if ( $hyperlinkObject != 0 ) {
		$obj1name = "<a href=\"" . $objectUrl . "?object=" . $obj1 . "\">" . $ObjectName[$obj1] . "</a>" ;
	} else {
		$obj1name = $ObjectName[$obj1] ;
	}
	$ana = &starts_with_vowel($obj1name) ? "an" : "a" ;
	printf "<LI>Which characteristic does $ana <b>$obj1name</b> have?<BR>\n";
}

sub create_question_type3 {

	$countQuest = 0 ;
	do {
		$obj1 = &select_random_object() ;
		$char1 = &select_random_char_with_object($obj1,'+') ;
		$char2 = &select_random_char_with_object($obj1,'.') ;
		$questionHash = &make_question_hash('3');
	} while ( ($countQuest++ < 20) &&
		  ( $char1 == 0 || $char2 == 0 || exists($questionsAsked{$questionHash}) ) ) ;
	if ( $countQuest >= 20 ) { return 0 ; }
	$questionsAsked{$questionHash} = 1 ;

	if ( rand(2) >= 1 ) {
		$answerval = 2 ;
		# swap
		$temp = $char1 ; $char1 = $char2 ; $char2 = $temp ;
	} else {
		$answerval = 1 ;
	}
	&print_question_type3 ;
	printf "&nbsp;&nbsp;<INPUT type=\"radio\" name=\"u$qq\" value=\"1\"> A. <i>$chArray[$char1]</i><BR>\n";
	printf "&nbsp;&nbsp;<INPUT type=\"radio\" name=\"u$qq\" value=\"2\"> B. <i>$chArray[$char2]</i><BR>\n<P>\n";
	printf "<INPUT TYPE=\"hidden\" NAME=\"f$qq\" VALUE=\"3$vsplitter$char1$vsplitter$char2$vsplitter$obj1\">\n";

	# append answer string
	$qansval .= $answerval ;
	return 1 ;
}

#   For these two chars, char1 char2, which obj has both? obj1 or obj2.
sub print_question_type4 {
	printf "<LI>Which $objectTitle has both of these characteristics:<BR>\n&nbsp;&nbsp;<i>$chArray[$char1]</i><BR>&nbsp;&nbsp;<i>$chArray[$char2]</i>?<BR>\n";
}
sub create_question_type4 {
	# result of following code: $obj1 will have $char1 and $char2, $obj2 will have only $char1
	$countQuest = 0 ;
	do {
		$countObjMatch = 0 ;	# avoid race condition, just in case
		do {
			$obj1 = &select_random_object ;
			$obj2 = &select_random_object ;
		} while ( ($countObjMatch++ < 20) && ($obj1 == $obj2) ) ;

		$char1 = &select_random_char_from_objs($obj1,$obj2,'+') ;
		$char2 = &select_random_char_from_objs($obj1,$obj2,'.') ;
		$questionHash = &make_question_hash('4');
	} while ( ($countQuest++ < 20) && ($char1 == 0 || $char2 == 0 || exists($questionsAsked{$questionHash})) ) ;
	if ( $countQuest >= 20 ) { return 0 ; }
	$questionsAsked{$questionHash} = 1 ;

	if ( rand(2) >= 1 ) {
		$temp = $char1 ; $char1 = $char2 ; $char2 = $temp ;
	}

	if ( rand(2) >= 1 ) {
		$answerval = 2 ;
		# swap
		$temp = $obj1 ; $obj1 = $obj2 ; $obj2 = $temp ;
	} else {
		$answerval = 1 ;
	}
	&print_question_type4 ;
	printf "&nbsp;&nbsp;<INPUT type=\"radio\" name=\"u$qq\" value=\"1\"> A. <b>$ObjectName[$obj1]</b><BR>\n";
	printf "&nbsp;&nbsp;<INPUT type=\"radio\" name=\"u$qq\" value=\"2\"> B. <b>$ObjectName[$obj2]</b><BR>\n<P>\n";
	printf "<INPUT TYPE=\"hidden\" NAME=\"f$qq\" VALUE=\"4$vsplitter$char1$vsplitter$char2$vsplitter$obj1$vsplitter$obj2\">\n";

	# append answer string
	$qansval .= $answerval ;
	return 1 ;
}

#  For these two objs, obj1 obj2, which char is common to both? char1 or char2.
sub print_question_type5 {
	if ( $hyperlinkObject != 0 ) {
		$obj1name = "<a href=\"" . $objectUrl . "?object=" . $obj1 . "\">" . $ObjectName[$obj1] . "</a>" ;
		$obj2name = "<a href=\"" . $objectUrl . "?object=" . $obj2 . "\">" . $ObjectName[$obj2] . "</a>" ;
	} else {
		$obj1name = $ObjectName[$obj1] ;
		$obj2name = $ObjectName[$obj2] ;
	}
	$ana = &starts_with_vowel($obj1name) ? "an" : "a" ;
	printf "<LI>Which characteristic is common to both of these:<BR>\n";
	printf "&nbsp;&nbsp<b>$obj1name</b><BR>\n";
	printf "&nbsp;&nbsp<b>$obj2name</b>?<BR>\n";
}
sub create_question_type5 {
	# result of following code: $obj1 will have $char1 and $char2, $obj2 will have only $char1
	$countQuest = 0 ;
	do {
		$countObjMatch = 0 ;	# avoid race condition, just in case
		do {
			$obj1 = &select_random_object ;
			$obj2 = &select_random_object ;
		} while ( ($countObjMatch++ < 20) && ($obj1 == $obj2) ) ;

		$char1 = &select_random_char_from_objs($obj1,$obj2,'+') ;
		$char2 = &select_random_char_from_objs($obj1,$obj2,'.') ;
		$questionHash = &make_question_hash('5');
	} while ( ($countQuest++ < 20) && ($char1 == 0 || $char2 == 0 || exists($questionsAsked{$questionHash})) ) ;
	if ( $countQuest >= 20 ) { return 0 ; }
	$questionsAsked{$questionHash} = 1 ;

	if ( rand(2) >= 1 ) {
		$temp = $obj1 ; $obj1 = $obj2 ; $obj2 = $temp ;
	}

	if ( rand(2) >= 1 ) {
		$answerval = 2 ;
		# swap
		$temp = $char1 ; $char1 = $char2 ; $char2 = $temp ;
	} else {
		$answerval = 1 ;
	}
	&print_question_type5 ;
	printf "&nbsp;&nbsp;<INPUT type=\"radio\" name=\"u$qq\" value=\"1\"> A. <i>$chArray[$char1]</i><BR>\n";
	printf "&nbsp;&nbsp;<INPUT type=\"radio\" name=\"u$qq\" value=\"2\"> B. <i>$chArray[$char2]</i><BR>\n<P>\n";
	printf "<INPUT TYPE=\"hidden\" NAME=\"f$qq\" VALUE=\"5$vsplitter$char1$vsplitter$char2$vsplitter$obj1$vsplitter$obj2\">\n";

	# append answer string
	$qansval .= $answerval ;
	return 1 ;
}

sub make_question_hash {
	my $qtype ;
   	($qtype) = @_;
	my $qh ;
	$qh = sprintf "1$vsplitter";
	if ( $char1 < $char2 ) {
		$qh .= sprintf "$char1$vsplitter$char2$vsplitter" ;
	} else {
		$qh .= sprintf "$char2$vsplitter$char1$vsplitter" ;
	}
	if ( $obj1 < $obj2 ) {
		$qh .= sprintf "$obj1$vsplitter$obj2" ;
	} else {
		$qh .= sprintf "$obj2$vsplitter$obj1" ;
	}
}

sub starts_with_vowel {
	my $vword ;
   	($vword) = @_;
	my $startchar ;
	$startchar = lc(substr($vword,1,1));
	if ( $startchar =~ /[aeiou]/ ) {
		return 1 ;
	} else {
		return 0 ;
	}
}

sub select_random_object {
	# someday have to pick from trimmed list >>>>>
	return $objSelSet[int( rand( $numObjSelSet ) + 1 )] ;
}

sub select_random_char {
	return $charSelSet[int( rand( $numCharSelSet ) + 1 )] ;
}
sub select_random_object_with_char {
	my $charNum;
	my $selValue;
   	($charNum, $selValue) = @_;
	my $selCount;
	my $rr;
	$selCount = 0 ;
	undef *selObj;
	for ( $rr = 1 ; $rr <= $numObjSelSet ; $rr++ ) {
		if ( substr($ObjectData[$objSelSet[$rr]],$charNum,1) eq $selValue ) {
			$selObj[++$selCount] = $objSelSet[$rr] ;
		}
	}
	if ( $selCount <= 0 ) {
		return 0 ;
	}
	my $selIndex ;
	$selIndex = int( 1 + rand($selCount));
	return $selObj[$selIndex];
}
sub select_random_char_with_object {
	my $objNum;
	my $selValue;
   	($objNum, $selValue) = @_;
	my $selCount;
	my $rr;
	my $objDatString ;
	$objDatString = $ObjectData[$objNum] ;
	$selCount = 0 ;
	undef *selChar;
	for ( $rr = 1 ; $rr <= $numCharSelSet ; $rr++ ) {
		if ( substr($objDatString,$charSelSet[$rr],1) eq $selValue ) {
			$selChar[++$selCount] = $charSelSet[$rr] ;
		}
	}
	if ( $selCount <= 0 ) {
		return 0 ;
	}
	my $selIndex ;
	$selIndex = int( 1 + rand($selCount));
	return $selChar[$selIndex];
}
sub select_random_char_from_objs {
	my $objNum1;
	my $objNum2;
	my $selValue;
   	($objNum1, $objNum2, $selValue) = @_;
	my $selCount;
	my $rr;
	my $objDatString1 ;
	my $objDatString2 ;
	$objDatString1 = $ObjectData[$objNum1] ;
	$objDatString2 = $ObjectData[$objNum2] ;
	$selCount = 0 ;
	undef *selChar;
	for ( $rr = 1 ; $rr <= $numCharSelSet ; $rr++ ) {
		if ( substr($objDatString1,$charSelSet[$rr],1) eq '+' &&
		     substr($objDatString2,$charSelSet[$rr],1) eq $selValue ) {
			$selChar[++$selCount] = $charSelSet[$rr] ;
		}
	}
	if ( $selCount <= 0 ) {
		return 0 ;
	}
	my $selIndex ;
	$selIndex = int( 1 + rand($selCount));
	return $selChar[$selIndex];
}
sub quiz_questions_header {
       # Print HTTP header and opening HTML tags.                           #
        print "Content-type: text/html\n\n";
        print "<html>\n <head>\n";

        # Print out title of page                                            #
        if ($Config{'title'}) { print "  <title>$Config{'title'}</title>\n" }
        else                  { print "  <title>$objectTitleCaps Quiz</title>\n"        }

        print " </head>\n <body";

        # Get Body Tag Attributes                                            #
        &body_attributes;

        # Close Body Tag                                                     #
        print ">\n";

        # Print custom or generic title.                                     #
        if ($Config{'title'}) { print "   <h1>$Config{'title'}</h1>\n" }
        else { print "   <h1>$objectTitleCaps Quiz</h1>\n" }

        printf "<P>This quiz is formed by choosing from $numCharSelSet characteristics and $numObjSelSet $objectTitlePlural.\n";
}

sub quiz_questions_footer {
	if ( $quizFailed == 1 ) {
		return ;
	}
	printf "<INPUT TYPE=\"hidden\" NAME=\"qval\" VALUE=\"$qansval\">\n";

        print <<"(END HTML FOOTER)";
<P>
<INPUT type="submit" value="     Submit Answers     " align="middle">

<P>
If you want to clear your choices, hit <input type="reset" name="mybutton" value="Reset">
</form>
<P>
Use your browser's Back button if you want to change anything and try again.
(END HTML FOOTER)

}

####################################################

# quiz answers token/value pairs
# qans=# - number of questions
# qval=string - string has the correct answers (one value per question)
#    example: qans=2&u1=1&f1=1,50,407&u2=0&f2=1,36,44&qval=00
# u1=# - question number, and answer user selects
# f1=#,#,#,#,# - first number is type of question, second on is characteristics or objects in question
#   types of questions:
#   1,c#,o# = Does this obj1 have this char1? Yes or no.
#   2,c#,o#,o# = Which obj has this char1? obj1 or obj2.
#   3,c#,c#,o# = Which char does this obj1 have? char1 or char2.
#   4,c#,c#,o#,o# = For these two chars, char1 char2, which obj has both? obj1 or obj2.
#   5,c#,c#,o#,o# = For these two objs, obj1 obj2, which char is common to both? char1 or char2.
#
sub grade_quiz {
	# make list of characteristics by array location
	foreach $cc (keys %chNum) {
		$chArray[$chNum{$cc}] = $chTitle{$cc} ;
	}

	# $f is token, $Form{$f} is value string
	foreach $f (keys %Form) {

		# number of quiz questions
		if ( $f eq 'qans' ) {
			$numQuiz = $Form{$f};
		}
		
		# quiz answer string
		if ( $f eq 'qval' ) {
			$qansval = $Form{$f};
		}
		
		# quiz questions: user answers
		if ( substr($f,1,1) eq 'u' ) {
			$index = substr($f,2) ;
			$qUser[$index] = $Form{$f};	# 1 or 2; 0 (unset) means not answered
		}

		# quiz questions: format
		if ( substr($f,1,1) eq 'f' ) {
			$index = substr($f,2) ;
			$qFormat[$index] = $Form{$f};	# string of questionType, chars, and objs
		}
	}

	&quiz_answers_header;

	# score the quiz - quite easy, actually
	$numCorrect = $numIncorrect = $numUnanswered = 0;
	for ( $ii = 1 ; $ii <= $numQuiz ; $ii++ ) {
		if ( $qUser[$ii] == 0 ) {
			$numUnanswered++ ;
		} elsif ( $qUser[$ii] eq substr($qansval,$ii,1) ) {
			$numCorrect++ ;
		} else {
			$numIncorrect++ ;
		}
	}
	if ( $numUnanswered > 0 ) {
		printf "<H2>Results</H2>\n$numCorrect correct, $numIncorrect incorrect, and $numUnanswered %s not answered.\n", ($numUnanswered == 1) ? 'was' : 'were';
	} else {
		printf "<H2>Results</H2>\n$numCorrect correct and $numIncorrect incorrect.\n";
 	}
	if ( $numCorrect == $numQuiz && $numQuiz > 1 ) {
		printf "<BR>Congratulations on a perfect score!\n";
	}
	printf "<H2>Answer Key</H2>\n";

	$hyperlinkObject = 1 ;

	printf "<OL>\n";
	for ( $qq = 1 ; $qq <= $numQuiz ; $qq++ ) {
		@flist = split($vsplitter,$qFormat[$qq]) ;
		$currQuestion = $flist[1];
		if ( $currQuestion == 1 ) { &explain_question_type1; }
		elsif ( $currQuestion == 2 ) { &explain_question_type2; }
		elsif ( $currQuestion == 3 ) { &explain_question_type3; }
		elsif ( $currQuestion == 4 ) { &explain_question_type4; }
		else { &explain_question_type5; }
	}
	printf "</OL>\n";
	&quiz_answers_footer;
}

sub no_answer {
	# printf "<I>You declined to answer.</I><P>\n" ;
	printf "<P>\n";
}
	
sub explain_question_type1 {
	$char1 = $flist[2];
	$obj1 = $flist[3];
	&print_question_type1;
	printf "&nbsp;&nbsp;A. Yes<BR>\n";
	printf "&nbsp;&nbsp;B. No<BR>\n";
	printf "<P>Answer is <b>%s</b><BR>\n", ( substr($qansval,$qq,1) == 1 ) ? 'A. Yes' : 'B. No' ;
	if ( $qUser[$qq] == 0 ) {
		&no_answer ;
	} else {
		$isOK = ( substr($qansval,$qq,1) == $qUser[$qq] ) ? "Correct" : "Incorrect" ;
		#printf "<I>$isOK: your answer was <b>%s</b></I><P>\n", ( $qUser[$qq] == 1 ) ? 'A. Yes' : 'B. No' ;
		printf "<I>$isOK: your answer was <b>%s</b></I><P>\n", ( $qUser[$qq] == 1 ) ? 'A. Yes' : 'B. No' ;
	}
}

sub explain_question_type2 {
	$char1 = $flist[2];
	$obj1 = $flist[3];
	$obj2 = $flist[4];
	&print_question_type2;
	printf "&nbsp;&nbsp;A. <b><a href=\"" . $objectUrl . "?object=" . $obj1 . "\">$ObjectName[$obj1]</a></b><BR>\n";
	printf "&nbsp;&nbsp;B. <b><a href=\"" . $objectUrl . "?object=" . $obj2 . "\">$ObjectName[$obj2]</a></b><BR>\n<P>\n";
	
	if ( substr($qansval,$qq,1) == 1 ) {
		$correctString = "A. " . $ObjectName[$obj1] ;
	} else {
		$correctString = "B. " . $ObjectName[$obj2] ;
	}
	printf "<P>Answer is <b>$correctString </b><BR>\n";

	if ( $qUser[$qq] == 0 ) {
		&no_answer ;
	} else {
		$isOK = ( substr($qansval,$qq,1) == $qUser[$qq] ) ? "Correct" : "Incorrect" ;
		if ( $qUser[$qq] == 1 ) {
			$yourString = "A. " . $ObjectName[$obj1] ;
		} else {
			$yourString = "B. " . $ObjectName[$obj2] ;
		}
		printf "<I>$isOK: your answer was <b>$yourString</b></I><P>\n";
	}
}

sub explain_question_type3 {
	$char1 = $flist[2];
	$char2 = $flist[3];
	$obj1 = $flist[4];
	&print_question_type3;
	printf "&nbsp;&nbsp;A. <i>$chArray[$char1]</i><BR>\n";
	printf "&nbsp;&nbsp;B. <i>$chArray[$char2]</i><BR>\n<P>\n";

	if ( substr($qansval,$qq,1) == 1 ) {
		$correctString = "A. " . $chArray[$char1] ;
	} else {
		$correctString = "B. " . $chArray[$char2] ;
	}
	printf "<P>Answer is <b>$correctString </b><BR>\n";

	if ( $qUser[$qq] == 0 ) {
		&no_answer ;
	} else {
		$isOK = ( substr($qansval,$qq,1) == $qUser[$qq] ) ? "Correct" : "Incorrect" ;
		if ( $qUser[$qq] == 1 ) {
			$yourString = "A. " . $chArray[$char1] ;
		} else {
			$yourString = "B. " . $chArray[$char2] ;
		}
		printf "<I>$isOK: your answer was <b>$yourString</b></I><P>\n";
	}
}

sub explain_question_type4 {
	$char1 = $flist[2];
	$char2 = $flist[3];
	$obj1 = $flist[4];
	$obj2 = $flist[5];
	&print_question_type4;
	printf "&nbsp;&nbsp;A. <b><a href=\"" . $objectUrl . "?object=" . $obj1 . "\">$ObjectName[$obj1]</a></b><BR>\n";
	printf "&nbsp;&nbsp;B. <b><a href=\"" . $objectUrl . "?object=" . $obj2 . "\">$ObjectName[$obj2]</a></b><BR>\n<P>\n";
	
	if ( substr($qansval,$qq,1) == 1 ) {
		$correctString = "A. " . $ObjectName[$obj1] ;
	} else {
		$correctString = "B. " . $ObjectName[$obj2] ;
	}
	printf "<P>Answer is <b>$correctString </b><BR>\n";

	if ( $qUser[$qq] == 0 ) {
		&no_answer ;
	} else {
		$isOK = ( substr($qansval,$qq,1) == $qUser[$qq] ) ? "Correct" : "Incorrect" ;
		if ( $qUser[$qq] == 1 ) {
			$yourString = "A. " . $ObjectName[$obj1] ;
		} else {
			$yourString = "B. " . $ObjectName[$obj2] ;
		}
		printf "<I>$isOK: your answer was <b>$yourString</b></I><P>\n";
	}
}

sub explain_question_type5 {
	$char1 = $flist[2];
	$char2 = $flist[3];
	$obj1 = $flist[4];
	$obj2 = $flist[5];
	&print_question_type5;
	printf "&nbsp;&nbsp;A. <i>$chArray[$char1]</i><BR>\n";
	printf "&nbsp;&nbsp;B. <i>$chArray[$char2]</i><BR>\n<P>\n";

	if ( substr($qansval,$qq,1) == 1 ) {
		$correctString = "A. " . $chArray[$char1] ;
	} else {
		$correctString = "B. " . $chArray[$char2] ;
	}
	printf "<P>Answer is <b>$correctString </b><BR>\n";

	if ( $qUser[$qq] == 0 ) {
		&no_answer ;
	} else {
		$isOK = ( substr($qansval,$qq,1) == $qUser[$qq] ) ? "Correct" : "Incorrect" ;
		if ( $qUser[$qq] == 1 ) {
			$yourString = "A. " . $chArray[$char1] ;
		} else {
			$yourString = "B. " . $chArray[$char2] ;
		}
		printf "<I>$isOK: your answer was <b>$yourString</b></I><P>\n";
	}
}

sub quiz_answers_header {
       # Print HTTP header and opening HTML tags.                           #
        print "Content-type: text/html\n\n";
        print "<html>\n <head>\n";

        # Print out title of page                                            #
        if ($Config{'title'}) { print "  <title>$Config{'title'}</title>\n" }
        else                  { print "  <title>$objectTitleCaps Quiz Answers</title>\n"        }

        print " </head>\n <body";

        # Get Body Tag Attributes                                            #
        &body_attributes;

        # Close Body Tag                                                     #
        print ">\n";

        # Print custom or generic title.                                     #
        if ($Config{'title'}) { print "   <h1>$Config{'title'}</h1>\n" }
        else { print "   <h1>$objectTitleCaps Quiz Answers</h1>\n" }

        print "\n";
	printf "<form action=\"$objectUrl\" method=\"get\" name=\"quizform\">\n" ;
}

sub quiz_answers_footer {
	printf "<P>If you find any answers that you think are in error, please <a href=\"mailto:erich\@acm.org\">email me</a> and I will fix the program.\n";
	printf "<P>You can <a href=\"$htmlUrl$quizHtml\">take another quiz</a> if you wish, but you'll lose your settings.\n" ;
	printf "To reuse your preferences, hit your browser's Back button twice, then hit the 'Create a Quiz' button again.\n" ;
	printf "<P>You can also go to the <a href=\"$htmlUrl$idHtml\">$objectTitle identification page</a>.\n";
}

sub init {

    $objectUrl = "http://www.realtimerendering.com/cgi-bin/birds.cgi" ;

    $htmlUrl = "http://www.realtimerendering.com/birds/" ;

    $idHtml = "birds.html" ;

    $quizHtml = "birdquiz.html" ;

    $objectTitleCapsPlural = "Birds" ;
    $objectTitlePlural = lc($objectTitleCapsPlural);

    $objectTitleCaps = $objectTitleCapsPlural ;
    chop $objectTitleCaps ;
    $objectTitle = lc($objectTitleCaps);

    $numChar = 60 ;

$chTitle{'action,swimming'} = 'Swimming' ;
$chNum{'action,swimming'} = 1 ;
$chTitle{'action,walking'} = 'Walking, wading, running' ;
$chNum{'action,walking'} = 2 ;
$chTitle{'action,hopping'} = 'Hopping or climbing' ;
$chNum{'action,hopping'} = 3 ;
$chTitle{'action,perching'} = 'Still perching' ;
$chNum{'action,perching'} = 4 ;
$chTitle{'action,flying'} = 'Continuous flying' ;
$chNum{'action,flying'} = 5 ;
$chTitle{'size,larger'} = 'Larger than robin' ;
$chNum{'size,larger'} = 6 ;
$chTitle{'size,same'} = 'About same size as robin' ;
$chNum{'size,same'} = 7 ;
$chTitle{'size,smaller'} = 'Smaller than robin' ;
$chNum{'size,smaller'} = 8 ;
$chTitle{'shape,necklong'} = 'Neck long' ;
$chNum{'shape,necklong'} = 9 ;
$chTitle{'shape,taillong'} = 'Tail long' ;
$chNum{'shape,taillong'} = 10 ;
$chTitle{'shape,tailforked'} = 'Tail forked' ;
$chNum{'shape,tailforked'} = 11 ;
$chTitle{'shape,billlong'} = 'Bill long, as long or longer than head' ;
$chNum{'shape,billlong'} = 12 ;
$chTitle{'shape,billthick'} = 'Bill thick, as thick or thicker at base than length of bill' ;
$chNum{'shape,billthick'} = 13 ;
$chTitle{'shape,headcrested'} = 'Head crested' ;
$chNum{'shape,headcrested'} = 14 ;
$chTitle{'color,white'} = 'Mostly white' ;
$chNum{'color,white'} = 15 ;
$chTitle{'color,black'} = 'Mostly blackish, or dark gray, bluish black, etc.' ;
$chNum{'color,black'} = 16 ;
$chTitle{'color,blackandwhite'} = 'Mostly black and white, or other dark color and white' ;
$chNum{'color,blackandwhite'} = 17 ;
$chTitle{'color,brown'} = 'Mostly brownish, or with many brown streaks or spots' ;
$chNum{'color,brown'} = 18 ;
$chTitle{'color,green'} = 'Mostly dull green or brownish green' ;
$chNum{'color,green'} = 19 ;
$chTitle{'color,rust'} = 'Rust color present' ;
$chNum{'color,rust'} = 20 ;
$chTitle{'color,red'} = 'Red present' ;
$chNum{'color,red'} = 21 ;
$chTitle{'color,yellow'} = 'Yellow or orange' ;
$chNum{'color,yellow'} = 22 ;
$chTitle{'color,blue'} = 'Blue or bright green (not dull green)' ;
$chNum{'color,blue'} = 23 ;
$chTitle{'markings,round'} = 'Round spots on body' ;
$chNum{'markings,round'} = 24 ;
$chTitle{'markings,streaks'} = 'Streaks (long spots)' ;
$chNum{'markings,streaks'} = 25 ;
$chTitle{'markings,cross'} = 'Cross barring' ;
$chNum{'markings,cross'} = 26 ;
$chTitle{'markings,plain'} = 'Underparts plain' ;
$chNum{'markings,plain'} = 27 ;
$chTitle{'markings,bold'} = 'Bold markings present (patches or blotches of black, white, or color)' ;
$chNum{'markings,bold'} = 28 ;
$chTitle{'markings,head'} = 'Head stripes or bands' ;
$chNum{'markings,head'} = 29 ;
$chTitle{'markings,crown'} = 'Crown patch' ;
$chNum{'markings,crown'} = 30 ;
$chTitle{'markings,eye'} = 'Eye ring' ;
$chNum{'markings,eye'} = 31 ;
$chTitle{'markings,tailstripes'} = 'Tail stripes (along)' ;
$chNum{'markings,tailstripes'} = 32 ;
$chTitle{'markings,tailbands'} = 'Tail bands (across)' ;
$chNum{'markings,tailbands'} = 33 ;
$chTitle{'markings,wingbands'} = 'Wing bands or bars' ;
$chNum{'markings,wingbands'} = 34 ;
$chTitle{'whenwhere,northsummer'} = 'North summer (June through August)' ;
$chNum{'whenwhere,northsummer'} = 35 ;
$chTitle{'whenwhere,northwinter'} = 'North winter (November through February)' ;
$chNum{'whenwhere,northwinter'} = 36 ;
$chTitle{'whenwhere,southsummer'} = 'South summer (June through August)' ;
$chNum{'whenwhere,southsummer'} = 37 ;
$chTitle{'whenwhere,southwinter'} = 'South winter (November through February)' ;
$chNum{'whenwhere,southwinter'} = 38 ;
$chTitle{'habitat,woods'} = 'Wood habitat' ;
$chNum{'habitat,woods'} = 39 ;
$chTitle{'habitat,fields'} = 'Field habitat' ;
$chNum{'habitat,fields'} = 40 ;
$chTitle{'habitat,marshes'} = 'Marsh habitat' ;
$chNum{'habitat,marshes'} = 41 ;
$chTitle{'habitat,flats'} = 'Flats or beach habitat' ;
$chNum{'habitat,flats'} = 42 ;
$chTitle{'location,flyhigh'} = 'Continuous flying high (near or above treetops when flying)' ;
$chNum{'location,flyhigh'} = 43 ;
$chTitle{'location,flylow'} = 'Continuous flying low (below treetops when flying)' ;
$chNum{'location,flylow'} = 44 ;
$chTitle{'location,perchhigh'} = 'Perched high (generally above middle of trees when perched or foraging)' ;
$chNum{'location,perchhigh'} = 45 ;
$chTitle{'location,perchlow'} = 'Perched low (generally below middle of trees when perched or foraging)' ;
$chNum{'location,perchlow'} = 46 ;
$chTitle{'location,ground'} = 'On ground (walking, wading, running, hopping, or resting on ground)' ;
$chNum{'location,ground'} = 47 ;
$chTitle{'behavior,soaring'} = 'Soaring flight (gliding or circling on set wings)' ;
$chNum{'behavior,soaring'} = 48 ;
$chTitle{'behavior,zigzag'} = 'Zig zag flight (many irregular twists and turns)' ;
$chNum{'behavior,zigzag'} = 49 ;
$chTitle{'behavior,bounding'} = 'Bounding flight' ;
$chNum{'behavior,bounding'} = 50 ;
$chTitle{'behavior,forays'} = 'Short forays (flies out from perch and returns)' ;
$chNum{'behavior,forays'} = 51 ;
$chTitle{'behavior,jerks'} = 'Jerks tail or body (repeated dipping of body, or flipping or pumping of tail)' ;
$chNum{'behavior,jerks'} = 52 ;
$chTitle{'behavior,flocks'} = 'Occurs in flocks (from 4 or 5 to thousands)' ;
$chNum{'behavior,flocks'} = 53 ;
$chTitle{'calls,harsh'} = 'Rasping harsh calls' ;
$chNum{'calls,harsh'} = 54 ;
$chTitle{'calls,clear'} = 'Smooth, clear calls (can be imitated by human singing voice or whistling)' ;
$chNum{'calls,clear'} = 55 ;
$chTitle{'calls,soft'} = 'Soft, low calls' ;
$chNum{'calls,soft'} = 56 ;
$chTitle{'calls,staccato'} = 'Staccato and twitter call (short sharp notes or rapid series of notes: tinkling, trilling, sputtering, or percussive)' ;
$chNum{'calls,staccato'} = 57 ;
$chTitle{'song,high'} = 'High or thin song (high pitched and weak; lisping, sizzling, or hissing quality)' ;
$chNum{'song,high'} = 58 ;
$chTitle{'song,harsh'} = 'Harsh or buzzy song (pitch intermediate; rasping, buzzing, or grating quality)' ;
$chNum{'song,harsh'} = 59 ;
$chTitle{'song,melodious'} = 'Melodious song (pitch variable; smooth, sweet, or rich quality; pattern generally complex)' ;
$chNum{'song,melodious'} = 60 ;

    $NumObjects = 293 ;

    @ObjectName = (
'Common Loon, winter',
'Common Loon, summer',
'Red-throated Loon, winter',
'Red-necked Grebe',
'Western Grebe',
'Pied-billed Grebe',
'Horned Grebe, winter',
'Horned Grebe, summer',
'Eared Grebe',
'White Pelican',
'Double-breasted Cormorant',
'Anhinga/Water-turkey/Snakebird',
'Tundra Swan',
'Canada Goose',
'White-fronted Goose',
'Blue Goose',
'Snow Goose',
'Mallard, female',
'Mallard, male',
'Black Duck',
'Pintail, male',
'Pintail, female',
'Gadwall',
'American Widgeon, female',
'American Widgeon, male',
'Shoveller, female',
'Shoveller, male',
'Blue-winged Teal',
'Green-winged Teal',
'Wood Duck, female',
'Wood Duck, male',
'Redhead',
'Canvasback, female',
'Canvasback, male',
'Ring-necked Duck',
'Scaup, female',
'Scaup, male',
'Goldeneye, female',
'Goldeneye, male',
'Bufflehead',
'Oldsquaw',
'Ruddy Duck',
'Common Merganser, female',
'Common Merganser, male',
'Red-breasted Merganser, female',
'Red-breasted Merganser, male',
'Hooded Merganser',
'Turkey Vulture',
'Black Vulture',
'Goshawk',
'Cooper\'s Hawk',
'Sharp-shinned Hawk',
'Northern Harrier/Marsh Hawk',
'Rough-legged Hawk (light morph)',
'Rough-legged Hawk (dark morph)',
'Swainson\'s Hawk (light morph)',
'Broad-winged Hawk',
'Red-tailed Hawk, adult',
'Red-tailed Hawk, immature',
'Broad-winged Hawk',
'Red-shouldered Hawk',
'Golden Eagle',
'Bald Eagle, adult',
'Bald Eagle, immature',
'Osprey',
'Peregrine Falcon',
'Pigeon Hawk/Merlin',
'Sparrow Hawk/American Kestrel',
'Ruffed Grouse',
'Spruce Grouse',
'Lesser Prairie-Chicken',
'Greater Prairie-Chicken',
'Sharp-tailed Grouse',
'Bobwhite',
'Ring-necked Pheasant',
'Gray (Hungarian) Partridge',
'Great Egret',
'Snowy Egret',
'Cattle Egret',
'Great Blue Heron',
'Little Blue Heron',
'Black-crowned Night Heron',
'Yellow-crowned Night Heron',
'American Bittern',
'Least Bittern',
'Sandhill Crane',
'Sora',
'Virginia Rail',
'Gallinule',
'American Coot',
'Black-bellied Plover',
'American Golden Plover',
'Piping Plover',
'Semipalmated Plover',
'Killdeer',
'Whimbrel',
'Marbled Godwit',
'Solitary Sandpiper',
'Spotted Sandpiper',
'Greater Yellowlegs',
'Lesser Yellowlegs',
'Stilt Sandpiper',
'Upland Sandpiper',
'Red Knot',
'Long-billed & Short-billed Dowitcher',
'Ruddy Turnstone',
'Dunlin',
'Pectoral Sandpiper',
'Sanderling',
'Baird\'s Sandpiper',
'White-rumped Sandpiper',
'Semipalmated Sandpiper',
'Least Sandpiper',
'Western Sandpiper',
'Wilson\'s Phalarope',
'Common Snipe',
'American Woodcock',
'Herring Gull, immature',
'Herring Gull, adult',
'Ring-billed Gull, immature',
'Ring-billed Gull, adult',
'Franklin\'s Gull, adult',
'Bonaparte\'s Gull, adult',
'Common Tern',
'Forster\'s Tern',
'Caspian Tern',
'Black Tern',
'Mourning Dove',
'Rock Dove (Pigeon)',
'Yellow-billed Cuckoo',
'Black-billed Cuckoo',
'Screech Owl',
'Great Horned Owl',
'Long-eared & Short-eared Owl',
'Barn Owl',
'Snowy Owl',
'Barred Owl',
'Saw-whet Owl',
'Nighthawk',
'Chimney Swift',
'Ruby-throated Hummingbird',
'Belted Kingfisher',
'Yellow-shafted Flicker',
'Pileated Woodpecker',
'Red-headed Woodpecker',
'Red-bellied Woodpecker',
'Yellow-bellied Sapsucker',
'Downy Woodpecker',
'Hairy Woodpecker',
'Black-backed & Three-toed Woodpecker',
'Eastern Kingbird',
'Western Kingbird',
'Yellow-bellied Flycatcher',
'Eastern Phoebe',
'Acadian Flycatcher',
'Traill\'s Flycatcher',
'Least Flycatcher',
'Great Crested Flycatcher',
'Olive-sided Flycatcher',
'Eastern Wood-Pewee',
'Horned Lark',
'Barn Swallow',
'Cliff Swallow',
'Bank Swallow',
'Northern Rough-winged Swallow',
'Purple Martin',
'Tree Swallow',
'Blue Jay',
'Gray Jay',
'Common Raven',
'Common Crow',
'Black-capped Chickadee',
'Boreal Chickadee',
'Tufted Titmouse',
'Brown Creeper',
'Red-breasted Nuthatch',
'White-breasted Nuthatch',
'House Wren',
'Winter Wren',
'Bewick\'s Wren',
'Carolina Wren',
'Marsh Wren',
'Northern Mockingbird',
'Catbird',
'Brown Thrasher',
'American Robin',
'Wood Thrush',
'Veery',
'Hermit Thrush',
'Swainson\'s Thrush',
'Gray-Cheeked Thrush',
'Bluebird',
'Blue-gray Gnatcatcher',
'Golden-crowned Kinglet',
'Ruby-crowned Kinglet',
'Pipit',
'Cedar Waxwing',
'Bohemian Waxwing',
'Loggerhead Shrike',
'Northern Shrike',
'Starling',
'Solitary Vireo',
'White-eyed Vireo',
'Bell\'s Vireo',
'Yellow-throated Vireo',
'Red-eyed Vireo',
'Philadelphia Vireo',
'Warbling Vireo',
'Black and White Warbler',
'Protonotary Warbler',
'Blue-winged Warbler',
'Golden-winged Warbler',
'Tennessee Warbler',
'Orange-crowned Warbler',
'Nashville Warbler',
'Parula Warbler',
'Yellow Warbler',
'Magnolia Warbler',
'Cape May Warbler',
'Myrtle Warbler',
'Black-throated Green Warbler',
'Black-throated Blue Warbler',
'Cerulean Warbler',
'Blackburnian Warbler',
'Chestnut-sided Warbler',
'Bay-breasted Warbler',
'Blackpoll Warbler',
'Pine Warbler',
'Prarie Warbler',
'Palm Warbler',
'Ovenbird',
'Northern Waterthrush',
'Louisiana Waterthrush',
'Yellowthroat',
'Yellow-breasted Chat',
'Hooded Warbler',
'Kentucky Warbler',
'Connecticut Warbler',
'Mourning Warbler',
'Wilson\'s Warbler',
'Canada Warbler',
'American Redstart',
'House (English) Sparrow',
'Bobolink, male',
'Bobolink, female',
'Dickcissel',
'Meadowlark',
'Red-winged Blackbird, male',
'Red-winged Blackbird, female',
'Yellow-headed Blackbird',
'Rusty Blackbird',
'Brewer\'s Blackbird',
'Common Grackle',
'Brown-headed Cowbird',
'Orchard Oriole',
'Baltimore Oriole',
'Scarlet Tanager',
'Summer Tanager',
'Cardinal',
'Rose-breasted Grosbeak',
'Evening Grosbeak',
'Blue Grosbeak',
'Indigo Bunting',
'Purple Finch',
'Pine Grosbeak, male',
'Pine Grosbeak, female',
'White-Winged Crossbill, male',
'White-Winged Crossbill, female',
'Common Redpoll',
'Pine Siskin',
'Evening Grosbeak',
'American Goldfinch',
'Red Crossbill',
'Rufous-sided Towhee',
'Henslow\'s Sparrow',
'Grasshopper Sparrow',
'Savannah Sparrow',
'Vesper Sparrow',
'Lark Sparrow',
'Slate-colored Junco',
'Tree Sparrow',
'Chipping Sparrow',
'Clay-colored Sparrow',
'Field Sparrow',
'Harris\' Sparrow',
'White-Throated Sparrow',
'White-Crowned Sparrow',
'Fox Sparrow',
'Song Sparrow',
'Lincoln Sparrow',
'Swamp Sparrow',
'Lapland Longspur',
'Snow Bunting'
);

@ObjectData = (
  '+...++.....+....+.........+..........+....++..........+.....',
  '+...++.....+...++......+..++......+.......++..........+.....',
  '+...++.....+....+.........+..........+....++........+.......',
  '+...++..+..+.+..+..+......+..+....+.....+.++................',
  '+...++..+..+....+.........+..+....+.....+.++................',
  '+...++......+...+..........+..+...+.+...+.++.......+..++...+',
  '+...++..+....+..+.........++.+..........+.++........+.......',
  '+...++..+....+.....+......++++....+.....+.++................',
  '+...++..+....+..+....+....++++....+.....+.++................',
  '+...++.....++.+.+.........++......+......+++..++....+.......',
  '+..+++..++.+.+.+.....+....+.......+.++..+++++++.....+.......',
  '+..+++..++.+...++....+....+.....++..++..+.++++++............',
  '++..++..+.....+...........+..............+++..+.....+..+....',
  '++..++..+........+.........++...+.+.++.+++++..+.....+..+....',
  '++..++..+........+.......+.+.+..+.......+.++..+.....+..+....',
  '++..++..+........+........++....+.......++++..+.....+..+....',
  '++..++..+.....+...........++............++++..+.....+..+....',
  '++..++...........+....+.+...+....+++++..+.++..+.....++......',
  '++..++.............+..+...++...+.+++++..+.++..+.....++......',
  '++..++.........+.+....+.+...+....+++++..+.++..+......+......',
  '++..++...+................+++..+..+.+.....++..+.............',
  '++..++...+.......+......+.........+.+.....++..+.............',
  '++..++...........+.+.............++.....+.++.........+......',
  '++..++.............+.............++.+.....++........+.+.....',
  '++..++.............+..+....+++...++.+.....++........+.+.....',
  '++..++.....+.....+....+.+........++.+.....++.........+......',
  '++..++.....+.......+..+....+...+.++.+.....++.........+......',
  '++..++................+.+..++....++.+...+.++..+.+...+...+...',
  '++..++.............+..+.+..++....+........++....+....++.....',
  '++.+++.......+.............+..+...+.+.+.+.+++++.+.....+.....',
  '++.+++.......+.....+..+....++.....+.+.+.+.+++++.+.....+.....',
  '++..++...........+.+.......+......+.......++........+.......',
  '++..++.....+.....+................+.......++........+.......',
  '++..++.....+..+....+.......+......+.......++........+.......',
  '++..++..........++.........+..+..++..+....++........+.......',
  '++..++...........+...............+...+....++........+.......',
  '++..++..........+..........+.....+...+....++........+.......',
  '++..++.......+...+........+........+.+....++........+.......',
  '++..++.......+..+.........++.......+.+....++........+.......',
  '++..++.......+..+..........+.........+....++........+.......',
  '++..++...+......++.........+.......+.+....++........+.......',
  '++..++.............+......++++....+.+...+.++........+.......',
  '++..++.....+.+...+.+......+......++..+....++........+.......',
  '++..++.....+....+...+.+...++.....++..+....++........+.......',
  '++..++.....+.+...+.+......+......++..+....++........+.......',
  '++..++.....+.+..+..+..+....+.....++..+....++........+.......',
  '++..++.....+.+..++.+.......++....++.+.+...++................',
  '...+++...+.....+....+.....+.......+.++++..+.+.++....+.......',
  '...+++.........++.........+.........++++..+.+.++....+.......',
  '...+++...+..............++..++..+.++.++...+++.+++.+.....+...',
  '...+++...+.......+.+....++...+..+.+.+++...+++.+++.+.....+...',
  '...+++...+.......+.+....++...+..+.+.+++...+++.+++.+.....+...',
  '...+++...+.......+......+.......+.++++.++..+.+++............',
  '...+++..........++......+..++...+..+.+.++.++++++......+.....',
  '...+++.........+.+........++....+..+.+.++.++++++......+.....',
  '...+++..........++.+......++....+.+.+..+..++++++......+.....',
  '....++...........+......++......+.+.+.++..++..++......+.....',
  '...+++.........+.+.+....+........++.++++..+++.++.....+......',
  '...+++.........+.+......+.......+++.++++..+++.++.....+......',
  '...+++...........+.+....++......+.+.+.+...+.+..+..+.+.+.....',
  '...+++...........+.+....++......+.+.++++..+++.++.....++.....',
  '...+++.........+.+........+.....+..+.+.+..+.+..+.....+......',
  '...+++.........+++........++......+.+++++++.+.++.....+......',
  '...+++.........+.+........+.......+.+++++++.+.++.....+......',
  '...+++........+.++........+++...+.+.++..+++++.++......+.....',
  '...+++...+......++......++..+...+.+..+.++++.+..+........+...',
  '...+++...........+....+.+.......+.+..+++..+.+........+..+...',
  '...++++..........+.+..++++.+++..+.+.++.+..++++....++....+...',
  '.+...+.......+...+.+.....+......+.+++++......++....++..++...',
  '.+...+.........+.........+........++..+......++....++..++...',
  '.+...+...........+.......+........++++.+......+.....+..+....',
  '.+...+...........+.......+........++++..+.....+.....+..+....',
  '.+...+...+.......+......+......+..++++++......+.....+..+....',
  '.+...++..........+..........+.......++.+......+.+...+.+....+',
  '.+...+...+.......+.++.++++.+......++++.++.....+.....++......',
  '.+...+.............+.......+........++.+......+.....++......',
  '.+..++..+..+.+.......+............+.+.+.+++++.+.....++......',
  '.+..++..+..+.++......+..............+...++++..+.....+.......',
  '.+..++..+..+..+......+....+.........+..+++++..+.....+.......',
  '.+..++..+..+.+..........+...++....+.+++.+++++.++....++......',
  '.+..++..+..+..++....................+...++++..+.....+.......',
  '.+..++..+..+.+..++.....++.++.+....+.+++.+.+++++.....++......',
  '.+..++..+..+.+..++++.+.++..+++....+.+.+.+.+++++....+.+......',
  '.+...+..+..+.....+.+....+...+.....+..+..+.....+......+.+....',
  '.+...+..+..+.....+...+..+....+....+.++..+.....+......+.+....',
  '.+..++..+..+........+.....+..+....+.+..++.++..++....++......',
  '.+....++....+....+....+..+++......+.++..+.....+.+..+..+.+...',
  '.+....+++..+.....+.+.+....+.......+.++..+.....+.+..+....+...',
  '++...+......+..+....+.....++......+.+...+.....+....+.+......',
  '++...+......+..+..........+....+..+.++..+.....+....+++.+....',
  '.+....+.........++.....+.++++............+....+.....+.+.....',
  '.+....+..........+...+.+.++++..........+.+....+.....+.+.....',
  '.+.....+......+..........+.+......++.+...+....+.+...+.++....',
  '.+.....+.........+.......+.++........+..++....+.+...++..+...',
  '.+..+.+..........+.+.....+.++..+.++.++.+++++..+.+..+..+.+...',
  '.+...+..+..+.....+.......+..++..+....+..++....+.......+.....',
  '.+...+..+..+.....+.......+......+.+..+.+++....+.......+.....',
  '.+....+.+..+....++.....+....+..++.+.+....+....+....+..+.+...',
  '.+.....+...+.....+.....+..+.+.....+.++...+....+....+..+.+...',
  '.+...+..+..+.....+...+.+........+.......++....+....++.+.....',
  '.+...++.+..+.....+...+.+........+.......++....+....++.+.....',
  '.+....+.+..+.....+..........+...........++....++...+..+.....',
  '.+...++.+..+.....+................+.+..+......++...+..+.....',
  '.+....+....+.....+.+....+.+.....++...+...+....+.+...+.+.+...',
  '.+....+....+.....+.+....+...+.+.++...+...+....+.+...+.+.+...',
  '.+....+..........+.+.......++...++.......+....+.+...+.+.+...',
  '.+....++...+.....+.+....+..+...+.........+....+.+...+.+.+...',
  '.+....++...+.....+.+....+......+........++....+.+...+...+...',
  '.+....++...+.....+.+...........+.....+...+....+.+...+...+...',
  '.+....++...+.....+.....+..+..............+....+.+...+...+...',
  '.+....++...+.....+......+.......+........+....+.+...+...+...',
  '.+.....+...+.....+......+......+.........+....+.+...+...+...',
  '.+.....+...+.....+......+......+.....+..++....+.+...+...+...',
  '.+.....+...+.....+.+....+......+.....+...+....+.+...+...+...',
  '+.....+.+..+.......+......+++.....+.+...++....+....+.+.+....',
  '.+..+.+....+.....+......+...+.....+.++..+.++..+.+....+......',
  '.+....+....+.....+.+......+.+++...+.+.+.......+.+....+.....+',
  '++..++...........+......+.+.....+.++.+.+++++..++....+.++....',
  '++..++........+.+...++....++......++.+.+++++..++....+.+.....',
  '++..++...........+......+.......+.++++.+++++..++....+.+.....',
  '++..++........+......+....+.......++++.+++++..++....+.+.....',
  '++..++........+.+.........++.++.+.+....++.++..++....+.+.....',
  '.+..++........+.+.........++.+...+......++.+..+.....+.......',
  '....++...+++..+.....+.....+..+....+.+...++.+..+.+...++......',
  '....++...+++..+.....+.....+..+....+.....++.+..+.+...++......',
  '....++...+++.++.....+....+...+....+......+.+..+.....++......',
  '....++....++..+++.........+.......+.+...+.++..+.+...++..+...',
  '.+.++++..+.......+.....+..+....+..++++++..+++++....++..+....',
  '.+.++++...................+.......++++.+..++..+.....+..+....',
  '...+..+..+.+.....+.+......+...+.+.+.+.+.....++..........+...',
  '...+..+..+.+.....+........+...+.+.+.+.+.....++..........+...',
  '...+.+.......+...+.+....++....+...+++++.....++........+.....',
  '...+.+.......+...+.......+......+.+++++.....+..........+....',
  '...+.+.......+...+......+.........+.+++++...+++.+...........',
  '...+.+........+..+.+...+......+.....++.++...+........+......',
  '...+.+........+..+.......+.........+..++++..+++........+....',
  '...+.+...........+......+.....+...++++++++..+++........+....',
  '...+.+...........+......+.........+++++......+.......+......',
  '....+.+...+......+.......+......+++.+..+..+...+.+...++.+....',
  '....+..+.......+.+........+.......+.+..++++....++...+...+...',
  '....+..+...+......+.+.+...........+.+.+....+....+.......+...',
  '...+..+....+.+.....+..+..+.+......+.++.+.+...+....+..+..+...',
  '..+...+....+.....+..++.+.+.+++..+.+.++++....+++..+.+.++.+...',
  '..+..+..+..+.+.++...+......+++....+++++.....++........+.....',
  '..+...+....+....+...+.....++.....++.++++....+....++..++.....',
  '..+...+....+....+...+....+++.+...++.++++....+....++..++.....',
  '..+...+....+....+...+....+.+++.+.++..++.....++...+....+.....',
  '..+....+........+...+....+++++.+..+++++.....++...+......+...',
  '..+...+....+....+...+....+++++.+..+++++.....++...+......+...',
  '..+...+........++....+...+.+.+.+..++..+.....+....+......+...',
  '...+..+......+..+.........+..+..+.+.+..+.....+....+.....++..',
  '...+..+......+..+....+....+..+.+..+.+..+.....+....+.....++..',
  '...+...+..........+..+....+...+..++...+......+....+...+....+',
  '...+...+..................+......++.+.+.+....+....+.....+.+.',
  '...+...+.....+....+.......+...+..++.+.+.+....+....+.....+.+.',
  '...+...+..........+.......+...+..++.+...+....+....+.....+.+.',
  '...+...+.....+............+...+..++...+.....++....+..+..+.+.',
  '...+..++.....+.....+.+....+......++.+.+.....++....+..+..+.+.',
  '...+..++.....+....+.....+.........+...+.....+.....+...+....+',
  '...+..++.....+....+.......+......++.+.+.....+.....+...+....+',
  '.+..+..+.....+...+...+....++++.+..++++.+.+++..++.+..+...++..',
  '...++..+.++........+..+....+......+.+..+++.+++..+...+.+.+..+',
  '...++..+...........+.++....+.+....+.+..+++++++..+...+.+.+...',
  '...++..+..+......+.........+......+.+..+++.+++..+...+...+...',
  '...++..+..+......+................+.+..+++.+++..+...+...+...',
  '...++..+..+....+......+...+.......+.+..+++++++.++...+.+.....',
  '...++..+..+.....+.....+...+.......+.+..+++.+++..+...+...+...',
  '..+..++..+...+........+...+.+..++++++++.....+++.....+++.....',
  '..+...+..+......+.........+..+....++..+.....+++......++.....',
  '...+.+...+.+...+..........+.......++..+.....++++.....+......',
  '...+++.........+..........+.......+++++++++++.+.....++......',
  '..+....+.+......+..........+.+....+++++.+...++......+++.+..+',
  '..+....+.+.................+.+....++..+.+....+......+++.+...',
  '..+....+.....+..+..+................+++.....++.......++.+..+',
  '..+....+...+.....+......+.+.+.....+..++.....++...+....+..+..',
  '..+....+...+.......+......+.++....+..++.....++...+....+..+..',
  '..+....+...+....+.........+..+....+++++.....++...+....+.....',
  '..+....+...+.....+.......+........+.+.+......+.....+.+..+..+',
  '..+....+...+.....+.......+........+..++......++....+.....+.+',
  '..+....+.+.+.....+..........+..+....+++......++....+....+..+',
  '..+....+.+.+.....+.+........+.......+++......++....+....+..+',
  '..+....+...+.....+......+...+.....+.+..++....++..+.+.+..+.+.',
  '.++...+..+.+....+.........++...+.+..++++....+++....+.+..+..+',
  '.++...++.+.+...+...+......+..+....+.+.+......+.......+.....+',
  '.++..++..+.+.....+.+....+........++.+.++.....++......+..+..+',
  '.++...+............++.....+...+...+.++++....+++....+++..+..+',
  '.++...++.........+.+...+......+...+.+.+.....+++.........+..+',
  '.++...++.........+.+...+..........+.+.+......++......+..+..+',
  '.++...++.........+.+...+..........+..++......++....+.+..+..+',
  '.++...++.........+.....+......+...+...+......++.........+..+',
  '.++...++.........+.....+......+.......+......++.........+..+',
  '...+..++...........++.+...........+.+..+.....+....+...+....+',
  '..+....+.+.+....+.........+.+.++....+.+.....++....++.+....+.',
  '..+....+..........+.++....+.++...++..++.....++....+++...++..',
  '..+....+.....+....+.+.....+...+..++..++.....++....++++..++.+',
  '.+.....+.........+...+..+...+..+..+..+.+......+..+.++...+...',
  '...+..++.....+...+..++....+.+...+.+++++.....++....+.+.+..+..',
  '...+..++.....+...+.+++....+.+...++.+..+.....++....+.+.+..+..',
  '...+..+.........+.........+++..+.+..++.+....++....+..+.....+',
  '...+..+.........+.........+++..+.+.+...+....++....+..+.....+',
  '.+.+..++...+...+.....+.+..+.......++++++....+.+++...+++...++',
  '..+....+..........+.......+...+..++...+.....++.......+.....+',
  '..+....+..........+..+....+...+..+..+++......+.......+....+.',
  '..+....+..........+..+....+......+..+.+......+.......+.....+',
  '..+....+..........+..+....+...+..++.+.+.....+........+....++',
  '..+....+..........+.......+.++....+.+.+.....++.......+.....+',
  '..+....+..........+.......+.+.....+...+.....++.......+.....+',
  '..+....+..........+.......+.+.....+.+.+.....++.......+.....+',
  '..+....+........+.......+...+....++.+.+.....++...........+..',
  '..+....+.............+..............+.+.+....+.............+',
  '..+....+.............+....+.+....++.+.+......+............+.',
  '..+....+.............+....++++....+...+......+............+.',
  '..+....+..........+.......+.+.....+...+.....++..........+..+',
  '..+....+..........+..+....+...........+......+..........++..',
  '..+....+..........+..+....+...+...+...+.+....+.............+',
  '..+....+...........+.++....+..+..++...+.....+.............+.',
  '..+....+............++..+.........+.+.+.....++.............+',
  '..+....+.............+..+..++..++++...+.....++.............+',
  '..+....+...........+.+..+..+.....++...+.....+............+..',
  '..+....+........+....+..+..+++...++..++.....++....+.+...+..+',
  '..+....+..........+..+..+..+.....++...+.....++............+.',
  '..+....+.......++.....+....+......+...+......+............+.',
  '..+....+..............+.+........+..+.+.....+.............+.',
  '..+....+.............+..+..++....++...+.....+............+..',
  '..+....+...........+.+....++++...++...+......+.............+',
  '..+....+..........++.......+.....++...+.....+............+..',
  '..+....+........+.+.....+....+...++...+.....++..........++..',
  '..+....+..........+..+..+........++.+.+.....++..........+..+',
  '..+....+..........+..+..+...+....+..+.+.....++............+.',
  '..+....+...........+.+..+...++....+...+++....++....++...+..+',
  '.++....+.........+.+.+..+...++....+.+.+......++....+.......+',
  '..+....+.........+......+...+.....+...+......++....+.......+',
  '..+....+.........+......+...+.....+.+.+......++....+.......+',
  '..+....+.............+....+++.....+.+.+++....++..+...+..+..+',
  '..+....+.+...........+....+...+.....+.+......+.......+.....+',
  '..+....+.............+....++..++....+.+......++............+',
  '..+....+.............+....+++.+.....+.+......++............+',
  '..+....+.............+....+...+...+...+......++............+',
  '..+....+.............+....++......+...+......++............+',
  '..+....+.............+....+..+....+...+......+..........+..+',
  '..+....+.............+..+.....+...+...+......+.............+',
  '..+....+............++....++...++++.+.+.....++....++....++.+',
  '..+....+....+....+......+.++++...+++++.+....+++.....++....+.',
  '...+..++........+....+.....+......+.+..+.....+.+....+...+.++',
  '...+..++.........+...+..+...+.....+.+..+.....+.+....+...+.++',
  '..++..++....+....+.+.+.....++.......+..+.....+.......+...+..',
  '.+.+..+....+.....+...+..+..++.++..+.++.+....+++....++++.+..+',
  '...+..+........+....++....++.....++.++.++....++..+.+++.....+',
  '...+..+..........+......+.........+.++.++....++..+.+++....+.',
  '...+..+........+.....+....++.....++.++.++....++..+.+++....+.',
  '.+....+.....+..+..........+.......+..++++...+++....++++...+.',
  '.+....+.....+..+..........+.......+.+.+++...+++....++++...+.',
  '.+.+.++..+.+..++..........+.......+.++++....+++.....++....+.',
  '.+.+..++....+..+..........+.......+.+.+++...+++.....+++...+.',
  '..+...++...........+.+....++.....+..+.+.....+........+.....+',
  '..+...+..............+....++...+.++.+.+.....+.........+....+',
  '..+...+...........+.++....++......+.+.+.....+........+..+.++',
  '..+...+...........+.++....+.......+.+.+.....+.............+.',
  '..+...+..+..++...++.+.....+.......+++++......+.....+..+.+..+',
  '..+...+.....+...++..++..+..++....++.+.+.....++..........+..+',
  '..+...++....+....+...+....++++...+++.++.+....++.....+.+.....',
  '..+....+....+....+....+...+......+..+..+.....+.............+',
  '..+....+....+....+....+...+.......+.+.++....++..........+..+',
  '..++...+..+.+....+..+...+...+....+++.++.....+++.....+...+..+',
  '..+...+.....+.......+.....+......+++.++.....++......+.......',
  '..+...+.....+....+........+......+++.++.....++......+.......',
  '..+...++..+.+.......+.....+......+++.++.....++......+.......',
  '..+...++..+.+....+...+..+........+++.++.....++......+.......',
  '..+....+..+.+.......+...+....+...+.+.++++....++..+..+...+...',
  '..+....+..+.+....+...+..+........+.+.++.....++...+..+...+...',
  '...+..+..........++..+....++.+...+++.+++....++......+.+.....',
  '..++...+..+.+.....+..+....++.+...++++++++...+++..+..+...+..+',
  '..+...++..+.+.......+............+++.++.....+++.......+.....',
  '..+...+..+..+...++.+.......+...+..+.+++......++.........+..+',
  '..+....+....+....+......+...++....+.++.+.....++.........+++.',
  '..+....+....+....+..........++....+.++.+.....++.........+++.',
  '..+....+....+....+......+...+.....+.++.+.....++.........+++.',
  '..+....+....+....+.+....+.....++..+.++.+.....++............+',
  '..+....+....+....+.+...++..++..+....+..+.....++............+',
  '..+....+....+...+.........+....+..++.++++....++..+..+...+..+',
  '..+....+....+....+.+...++.+.++...+.+.+.++....++.....+...+..+',
  '..+....+....+....+.+....+.+.++...++.+.+.....+++.........++..',
  '..+....+....+....+......+.+.+....++...++.....++.........+.+.',
  '..+....+....+....+......+.+..+...++.++.+.....++.........+..+',
  '..+....+....+....+......+..+.+...+....++.....++.....+...+...',
  '..+....+....+....+...+..+.+.++...++..+++.....++.....+.+.+..+',
  '..+....+....+....+........+.++...+...+.+.....++.....+.+.+..+',
  '..+....+....+....+.+...++.........+..++......++.........+..+',
  '..+....+....+....+.+...++...+.....+++++++....++.........+..+',
  '..+....+....+....+.....++...+.....+..++++....++.........+..+',
  '..+....+....+....+.+...++.+..+....+.++..+....++.........+..+',
  '.++....+....+....+.+.......+++.+.+.+.+.+.+....+..+..+...+...',
  '.++....+....+.+............+....++.+.+.+.+....+..+.++.+.+...'
);

}
