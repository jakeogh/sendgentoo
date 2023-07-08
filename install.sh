#!/bin/sh


emerge --sync
eselect repository add jakeogh git https://github.com/jakeogh/jakeogh
emerge --sync
CONFIG_PROTECT="-*" emerge --autounmask --autounmask-write --autounmask-continue sendgentoo
sendgentoosimple --help
