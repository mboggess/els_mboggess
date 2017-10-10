#!/bin/bash

# global functions
function get_num_pages_of_item()
{
        local __link=$1
        local __user_option="-u mboggess:1348911f703bacc837e8fc55fd73fee3aaa6f780"
        num_pages=0

        num_pages=`curl -s -I ${__user_option} ${__link} | grep Link: | awk '{print \$4}' | awk -F= '{print \$2}' | sed 's/>;$//'`
}

# global vars
USEROPTION="-u mboggess:1348911f703bacc837e8fc55fd73fee3aaa6f780"
ELSREPOURL="https://api.github.com/orgs/elsevierPTG/repos"
OUTPUTPATH="/Users/boggessm/elsevier/repo_branch_info"
CSSHEADER='<link href="txtstyle.css" rel="stylesheet" type="text/css" />'
DATAHEADER="BRANCH			LAST COMMIT DATE	LAST COMMIT AUTHOR	STATUS"

# !!!! REMEMBER THIS !!!!!
# Clear out old data files
rm -r $OUTPUTPATH/*.html
# !!!! REMEMBER THIS !!!!!

# Determine # of pages of repos for elsevierPTG
get_num_pages_of_item ${ELSREPOURL}
pages_of_repos=$num_pages

# Walk through each page of repos
#for page in $(seq 1 $pages_of_repos);
for page in $(seq 1 1);
do
	# Determine # of repos on page
	num_of_repos=$(curl -s $USEROPTION $ELSREPOURL?page=$page | jq '. | length')

	# Walk through each repo
        #for repo in $(seq 1 $num_of_repos);
	for repo in $(seq 1 2);
	do
		NAME=$(curl -s $USEROPTION $ELSREPOURL | jq ".[$repo] | .name" | sed 's/"//g')
		URL=$(curl -s $USEROPTION $ELSREPOURL | jq ".[$repo] | .url" | sed 's/"//g')
		OUTPUTFILE="$OUTPUTPATH/$NAME.html"

		echo "Repo: $NAME"

		# Print headers to output file
		echo "$CSSHEADER" >> $OUTPUTFILE
		echo "$DATAHEADER" >> $OUTPUTFILE

		# Determine # of pages of branches for current repo
		get_num_pages_of_item ${URL}/branches
		pages_of_branches=$num_pages

		# Walk through each page of branches
		for page in $(seq 1 $pages_of_branches);
		do
			# Determine # of branches on page
			num_of_branches=$(curl -s $USEROPTION $URL/branches?page=$page | jq '. | length')

			# Walk through each branch
			for branch in $(seq 1 $num_of_branches);
			do
				BRANCHNAME=$(curl -s $USEROPTION $URL/branches | jq ".[$branch] | .name" | sed 's/"//g')
				BRANCHURL="$URL/branches/$BRANCHNAME"
				BRANCHLASTCOMMITDATE=`curl -s ${USEROPTION} ${BRANCHURL} | jq '. | .commit.commit.author.date' | sed 's/"//g' | sed 's/Z$//'`
				# Determine if branch is active or stale
				current_date_seconds=$(date "+%s")
				if [ "$BRANCHLASTCOMMITDATE" != null ]; then
					last_commit_date_seconds=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$BRANCHLASTCOMMITDATE" "+%s")
					date_seconds_diff=$((current_date_seconds - last_commit_date_seconds))

					if [ "$date_seconds_diff" -lt 7776000 ]; then
						STATUS="active"
					else
						STATUS="STALE"
					fi
				else
					last_commit_date_seconds="null"
				fi

					
				BRANCHLASTCOMMITAUTHOR=`curl -s ${USEROPTION} ${BRANCHURL} | jq '. | .commit.commit.author.name' | sed 's/"//g'`

				# Print info to output file
				if [ "$BRANCHNAME" != "null" ]; then
					echo "${BRANCHNAME}			${BRANCHLASTCOMMITDATE}		${BRANCHLASTCOMMITAUTHOR}	${STATUS}" >> $OUTPUTFILE
				fi
			done
		done
	done
done

exit 0;
