#!/bin/bash
echo $1 $2
git checkout main
git fetch origin pull/$1/head:$2
dir="."
if test "$#" -gt "2"; then
    dir="$3"
fi
file=$(find $dir -name $2.fodt)
CHANGED=0
if test -n "$file"; then
  CHANGED=1
  libreoffice --headless --convert-to txt:Text $file --outdir /tmp/
  mv /tmp/$2.txt /tmp/"$2"_old.txt
fi
git checkout $2
if test "$CHANGED" -eq "1"; then
  libreoffice --headless --convert-to txt:Text $file --outdir /tmp/
  diff /tmp/"$2"_old.txt  /tmp/$2.txt
  libreoffice parts/main.fodt
else
  file=$(find . -name $2.fodt)
  if test -z "$file"; then
    libreoffice $file
  fi
fi
