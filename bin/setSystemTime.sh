#!/bin/bash

STATUS=/mnt/ramdisk/STATUS
POSITION=/mnt/ramdisk/POSITION

if [[ -r $STATUS  && -r $POSITION ]]; then
  FIX=$(awk '{print $2}' $STATUS)
  if [[ "$FIX" == TPV ]]; then
    DATETIME=$(awk -F, '{print $NF}' $POSITION)
    sudo date -s ${DATETIME}
  else
    echo "Did not find string TPV in $STATUS"
  fi
else
  echo "Could not read file $STATUS or $POSITION"
fi

exit 0
  
