#!/bin/sh

# PostgreSQL backup script for webscanner
# 121410 A NOV 2018 /PL @ Magenta Aps.

BACKUPDIR=/var/lib/os2webscanner/webscanner_backups
OUTFILE=postgresql-9.5-dumpall.sql.gz
BACKUPSTAMP="pg_dumpall.done"
LOGFILE="pg_dumpall.log"
#MAILTO=pl@magenta.dk
MAILTO=os2webscanner@magenta.dk

failed_move() {
mailx -s "Failed moving old backup" $MAILTO << EOF
Please check backup dir. and $LOGFILE
EOF
}

failed_dumpall() {
mailx -s "pg_dumpall failed" $MAILTO << EOF
Please check backup dir. and $LOGFILE
EOF
}

failed_rollback() {
mailx -s "Rollback failed" $MAILTO << EOF
Please check backup dir. and $LOGFILE
EOF/home/danni/postgresql-backup.sh
}

failed_delete_old() {
mailx -s "Failed deleting old backup" $MAILTO << EOF
Please check backup dir. and $LOGFILE
EOF
}

backup_succes() {
mailx -s "Postgresql backup succeeded" $MAILTO << EOF
Please check backup dir. and $LOGFILE
EOF
}

cd $BACKUPDIR
date >> $LOGFILE

mv $OUTFILE $OUTFILE.old
res=$?

if [ $res -ne 0 ];
   then
      failed_move
      echo "failed moving old backup to $OUTFILE.old" >> $LOGFILE
      exit $res
else
   /usr/bin/sudo -u postgres /usr/bin/pg_dumpall | /bin/gzip > $BACKUPDIR/$OUTFILE
   res2=$?
      if [ $res2 -ne 0 ];
         then
            failed_dumpall
            echo "pg_dumpall failed ..." >> $LOGFILE
            echo "Old backup file kept" >> $LOGFILE
            mv $BACKUPDIR/$OUTFILE.old $BACKUPDIR/$OUTFILE
            rollback=$?
               if [ $rollback -ne 0 ]
                  then
                     failed_rollback
                     "Cannot rollback ..." >> $LOGFILE
               else
                  echo "Rollback successful" >> $LOGFILE
               fi 
            exit $res2
      fi
   date >> $BACKUPDIR/BACKUPSTAMP
   rm $BACKUPDIR/$OUTFILE.old
   res3=$?
      if [ $res3 -ne 0 ]
         then
            failed_delete_old
            echo "could not delete $OUTFILE.old" >> $LOGFILE
            exit $res3
      fi
fi

backup_succes
echo "Backup succeeded" >> $LOGFILE
exit 0
