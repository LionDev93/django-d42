#!/bin/bash
/usr/bin/rsync --rsh='/usr/bin/ssh -p 422' -avzi  --exclude "*pyc" /home/shivji/d42/build/ damato@host13.device42.com:/home/damato/d42-build
