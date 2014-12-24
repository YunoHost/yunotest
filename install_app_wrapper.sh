#!/bin/bash

APP=$1
ARGS=$2
OUTPUT=$3

TMPDIR=$(mktemp -d)
TMP_SCRIPT=$TMPDIR/

# Setup sudoers env_file
cat << EOF > $TMPDIR/sudoers_env
#!/bin/sh
#export INSTW_DBGLVL=4
#export INSTW_DBGFILE=$TMPDIR/dbg
export INSTW_ROOTPATH=$TMPDIR
export INSTW_LOGFILE=$TMPDIR/newfiles.tmp
export INSTW_EXCLUDE="/dev,/proc,/tmp,/var/tmp,/var/cache/yunohost"
export LD_PRELOAD=/usr/lib/checkinstall/installwatch.so
EOF


# setup sudoers
cat << EOF > $TMPDIR/setup_sudoers
#!/bin/sh
if [ -z "\$1" ]; then
  #echo "Starting up visudo with this script as first parameter"
  export EDITOR=\$0 && sudo -E visudo
else
  # we are in visudo, and \$1 is the visudo tmp file
  # that will be validated/chmoded/... before replacing /etc/sudoers

  # comment Defaults	env_reset
  sed -e 's/\(Defaults.*env_reset\)/#\1/' -i \$1

  # add env_file
  sed "1s@^@Defaults env_file=$TMPDIR/sudoers_env\n@" -i \$1 
fi
EOF
chmod +x $TMPDIR/setup_sudoers

# teardown sudoers
cat << EOF > $TMPDIR/teardown_sudoers
#!/bin/sh
if [ -z "\$1" ]; then
  #echo "Starting up visudo with this script as first parameter"
  export EDITOR=\$0 && sudo -E visudo
else
  # we are in visudo, and \$1 is the visudo tmp file
  # that will be validated/chmoded/... before replacing /etc/sudoers

  # uncomment Defaults	env_reset
  sed -e 's/#\(Defaults.*env_reset\)/\1/' -i \$1
  # remove env_file
  sed '/Defaults.*env_file/d' -i \$1
fi
EOF
chmod +x $TMPDIR/teardown_sudoers

/bin/sh $TMPDIR/setup_sudoers
sudo yunohost app install -a "$ARGS" $APP
EXIT_STATUS=$?
/bin/sh $TMPDIR/teardown_sudoers

if [[ "$EXIT_STATUS" -ne "0" ]]; then
  rm -rf $TMPDIR
  exit $EXIT_STATUS
fi

sudo chown -R admin: $TMPDIR

cp ${TMPDIR}/newfiles.tmp ${TMPDIR}/newfiles.orig

echo "Extracting new files"
# regular files
cat ${TMPDIR}/newfiles.tmp | egrep -v '^[-0-9][0-9]*[[:space:]]*(unlink|access)' | cut -f 3 | egrep -v "^(/dev|/tmp)" | egrep "^/" | sort -u > ${TMPDIR}/newfiles
# symlinks
cat ${TMPDIR}/newfiles.tmp | egrep -v '^[-0-9][0-9]*[[:space:]]*(unlink|access)' | cut -f 4 | egrep -v "^(/dev|/tmp)" | grep -v "#success" | egrep "^/" | sort -u >> ${TMPDIR}/newfiles

# modified files
echo "Extracting modified files"
egrep "#success$" /${TMPDIR}/newfiles.tmp | cut -f 3 | sort -u  > ${TMPDIR}/modified
egrep "#success$" /${TMPDIR}/newfiles.tmp | cut -f 4 | egrep -v "#success" | sort -u >> ${TMPDIR}/modified

# OK, now we clean it up a bit
mv ${TMPDIR}/newfiles.tmp ${TMPDIR}/newfiles.installwatch
echo "Sorting..."
sort -u < ${TMPDIR}/newfiles | uniq > ${TMPDIR}/newfiles.tmp
mv ${TMPDIR}/newfiles.tmp ${TMPDIR}/newfiles

echo "Excluding some dirs..."
EXCLUDE="/var/cache/yunohost,/etc/sudoers,/etc/sudoers.d,/var/lib/apt,/var/cache/apt,/var/lib/dpkg"
for exclude in `echo $EXCLUDE | awk '{ split ($0, files,","); for(i=1; files[i] != ""; i++) print files[i];}'`; do
   if [ -d $exclude ]; then  # If it's a directory, ignore everything below it
      egrep -v "^$exclude" < ${TMPDIR}/newfiles > ${TMPDIR}/newfiles.tmp
   else
      if [ -f $exclude ]; then  # If it's a file, ignore just this one
         egrep -v "^$exclude$" < ${TMPDIR}/newfiles > ${TMPDIR}/newfiles.tmp
      fi
   fi
   mv ${TMPDIR}/newfiles.tmp ${TMPDIR}/newfiles
done

echo "Filtering non-existant files and files from deb packages..."
cat ${TMPDIR}/newfiles | while read file; do
    if sudo test -f $file ; then
      if (echo $file | grep "^/var/www" > /dev/null) ; then
        echo $file >> ${TMPDIR}/newfiles.tmp
      elif !(dpkg -S $file >/dev/null 2>&1) ; then
        echo $file >> ${TMPDIR}/newfiles.tmp
      fi
    elif sudo test -d $file ; then
      echo $file >> ${TMPDIR}/newfiles.tmp
    fi
	done
mv ${TMPDIR}/newfiles.tmp ${TMPDIR}/newfiles

echo "Getting permissions..."
cat ${TMPDIR}/newfiles | while read f; do
  (sudo stat $f --format="%A %U %G" | awk -F' ' '{printf("%10s %10s %10s     %s", $1, $2, $3, $4)}'; echo $f) >> ${TMPDIR}/newfiles.tmp
  done
mv ${TMPDIR}/newfiles.tmp ${TMPDIR}/newfiles

cp $TMPDIR/newfiles $OUTPUT

rm -rf $TMPDIR

exit $EXIT_STATUS
