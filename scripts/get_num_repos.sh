#!/bin/bash

# Need:
#  Link
#  Number of pages

# Then:
#  Loop through # of pages
#  use jq to count objects per page, keeping running total
#  return total # of repos from all pages

USEROPTION="-u mboggess:1348911f703bacc837e8fc55fd73fee3aaa6f780"
REPOLINK="https://api.github.com/orgs/elsevierPTG/repos"

function get_num_pages_of_item()
{
	local __link=$1
        local __user_option="-u mboggess:1348911f703bacc837e8fc55fd73fee3aaa6f780"
        num_pages=0

        num_pages=`curl -s -I ${__user_option} ${__link} | grep Link: | awk '{print \$4}' | awk -F= '{print \$2}' | sed 's/>;$//'`
}

        
# Determine # of pages of repos
get_num_pages_of_item ${REPOLINK}
echo "Total pages of repos: $num_pages"

page_repos=0
total_repos=0

for page in $(seq 1 $num_pages);
do
	page_repos=`curl -s ${USEROPTION} ${REPOLINK}?page=${page} | jq '. | length'`
	total_repos=$((total_repos + page_repos))
done

echo "Total repos: ${total_repos}"

exit 0;
