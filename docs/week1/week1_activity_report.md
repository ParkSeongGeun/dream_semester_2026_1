### 1주차 Todo

🔧 환경 구축

- [x] **1.** Ubuntu 22.04 LTS 설치
- [x] **2.** 파일시스템 계층 구조 이해 (`/`, `/home`, `/etc`, `/var`, `/usr`)

📂 파일 & 디렉토리 명령어

- [x] **3.** 탐색 명령어 실습 — `ls`, `cd`, `pwd`
- [x] **4.** 파일 조작 실습 — `cp`, `mv`, `rm`, `mkdir`, `touch`
- [x] **5.** 파일 내용 확인 — `cat`, `less`

🔐 권한 관리

- [x] **6.** 권한 체계 이해 — `rwx`, `chmod`, `chown`

✏️ 편집기 & 패키지 관리

- [x] **7.** `vim` 기본 사용법 (열기, 입력, 저장, 종료)
- [x] **8.** `apt` 패키지 관리자 실습

⚙️ 프로세스 & 자동화

- [x] **9.** 프로세스 관리 — `ps`, `top`, `kill`
- [x] **10.** Bash 스크립트 기초 — 변수, 조건문(`if`), 반복문(`for`, `while`)

🔑 SSH & 원격 접속

- [x] **11.** SSH 키 생성 및 키 기반 인증 설정

📝 최종 결과물

- [x] **12.** `setup.sh` 서버 초기화 스크립트 작성 (Python, Docker 설치 + 방화벽 설정)
- [x] **13.** 개인 명령어 치트시트 작성

---

## 🔧 환경 구축

### 1.  Ubuntu 22.04 환경 세팅

macOS를 이용하므로, VirtualBox Manager / UTM을 사용할 수 있지만, 현재 컴퓨터 용량이 부족해 위의 프로그램들을 설치하지 않고, 내가 오픈소스 기여를 했던 apple container를 사용한다.

**[환경 설정]**

먼저 Apple의 **container CLI**가 설치되어 있어야 한다. (macOS 26 Tahoe 기본 포함 또는 GitHub에서 설치)

그 후 ubuntu 22.04 이미지를 가져와 실행한다.

```bash
╭─░▒▓ ~/Desktop ▓▒░···················································░▒▓ ✔  system   10:44:08 ▓▒░─╮
╰─ container system start

╭─░▒▓ ~/Desktop ▓▒░···················································░▒▓ ✔  system   10:45:48 ▓▒░─╮
╰─ container run -it --rm ubuntu:22.04 /bin/bash

root@52c25463-0ea6-4e53-990c-36408481f246:/#                                                    ─╯
```

그럼 ubuntu 22.04 환경으로 진입한 것을 볼 수 있다. 한번 더 확인을 해보려면

`cat /etc/os-release`를 통해 환경을 확인할 수 있다.

```bash
root@52c25463-0ea6-4e53-990c-36408481f246:/# cat /etc/os-release
PRETTY_NAME="Ubuntu 22.04.5 LTS"
NAME="Ubuntu"
VERSION_ID="22.04"
VERSION="22.04.5 LTS (Jammy Jellyfish)"
VERSION_CODENAME=jammy
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=jammy
```

### 2. 파일시스템 계층 구조

리눅스 환경이 설정되었으니, 리눅스의 파일시스템 계층 구조에 대해 학습을 진행해보자. 먼저 아래 명령어를 입력해보자.

- Linux의 현재 디렉토리 파일 목록 확인: ls
- `ls /` : 최상위 디렉토리 목록 출력

```bash
root@52c25463-0ea6-4e53-990c-36408481f246:/# ls /
bin   dev  home  lost+found  mnt  proc  run   srv  tmp  var
boot  etc  lib   media       opt  root  sbin  sys  usr

root@52c25463-0ea6-4e53-990c-36408481f246:/# ls /home
root@52c25463-0ea6-4e53-990c-36408481f246:/# ls -a /home
.  ..

root@52c25463-0ea6-4e53-990c-36408481f246:/# ls /etc
adduser.conf            dpkg          issue          mke2fs.conf    rc1.d        shells
alternatives            e2scrub.conf  issue.net      netconfig      rc2.d        skel
apt                     environment   kernel         networks       rc3.d        subgid
bash.bashrc             fstab         ld.so.cache    nsswitch.conf  rc4.d        subuid
bindresvport.blacklist  gai.conf      ld.so.conf     opt            rc5.d        sysctl.conf
cloud                   group         ld.so.conf.d   os-release     rc6.d        sysctl.d
cron.d                  gshadow       legal          pam.conf       rcS.d        systemd
cron.daily              gss           libaudit.conf  pam.d          resolv.conf  terminfo
debconf.conf            host.conf     login.defs     passwd         rmt          update-motd.d
debian_version          hostname      logrotate.d    profile        security     xattr.conf
default                 hosts         lsb-release    profile.d      selinux
deluser.conf            init.d        machine-id     rc0.d          shadow

root@52c25463-0ea6-4e53-990c-36408481f246:/# ls /var
backups  cache  lib  local  lock  log  mail  opt  run  spool  tmp

root@52c25463-0ea6-4e53-990c-36408481f246:/# ls /usr
bin  games  include  lib  libexec  local  sbin  share  src
```

ls와 함께 각 디렉토리의 역할 또한 확인해볼 수 있다.

| 디렉토리 | 역할                    | 예시                         |
| -------- | ----------------------- | ---------------------------- |
| `/bin`   | 기본 실행 파일          | `ls`, `cp`, `cat` 등         |
| `/sbin`  | 시스템 관리용 실행 파일 | `reboot`, `fdisk` 등         |
| `/etc`   | 설정 파일 모음          | `hosts`, `passwd`, `apt/` 등 |
| `/home`  | 일반 사용자 홈 디렉토리 | `/home/username/`            |
| `/root`  | root 계정의 홈 디렉토리 | **지금 나는 여기 있다.**     |
| `/var`   | 자주 변하는 데이터      | 로그(`/var/log`), 캐시 등    |
| `/usr`   | 사용자 프로그램         | 설치된 앱들 대부분 여기      |
| `/tmp`   | 임시 파일               | 재부팅 시 삭제됨             |
| `/proc`  | 실행 중인 프로세스 정보 | 실제 파일 아님, 가상         |
| `/dev`   | 장치 파일               | 디스크, 키보드 등 하드웨어   |

---

## 📂 파일 & 디렉토리 명령어

### 1. 탐색 명령어 실습

하나씩 실행해보자. 명령어 → 결과 순이다.

1. 현재 위치 확인

```bash
pwd

root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:/# pwd
/
```

1. 홈 디렉토리로 이동

```bash
cd ~
pwd

root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:/# cd ~
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~# pwd
/root
```

1. 상위 디렉토리로 이동

```bash
cd ..
pwd

root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~# cd ..
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:/# pwd
/
```

1. ls 옵션들 실습

```bash
ls        # 기본 목록
ls -l     # 상세 정보 (권한, 소유자, 크기, 날짜)
ls -a     # 숨김 파일 포함
ls -lh    # 파일 크기를 보기 좋게 (KB, MB)
ls -la    # 상세 + 숨김 파일 모두
```

```bash
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:/# ls
bin   dev  home  lost+found  mnt  proc  run   srv  tmp  var
boot  etc  lib   media       opt  root  sbin  sys  usr

root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:/# ls -l
total 52
lrwxrwxrwx   1 root root    7 Feb 10 14:13 bin -> usr/bin
drwxr-xr-x   2 root root 4096 Apr 18  2022 boot
drwxr-xr-x   6 root root 2740 Mar  2 02:22 dev
drwxr-xr-x  32 root root 4096 Mar  2 02:22 etc
drwxr-xr-x   2 root root 4096 Apr 18  2022 home
lrwxrwxrwx   1 root root    7 Feb 10 14:13 lib -> usr/lib
drwx------   2 root root 4096 Mar  2 01:46 lost+found
drwxr-xr-x   2 root root 4096 Feb 10 14:13 media
drwxr-xr-x   2 root root 4096 Feb 10 14:13 mnt
drwxr-xr-x   2 root root 4096 Feb 10 14:13 opt
dr-xr-xr-x 114 root root    0 Mar  2 02:22 proc
drwx------   2 root root 4096 Feb 10 14:21 root
drwxr-xr-x   5 root root 4096 Feb 10 14:22 run
lrwxrwxrwx   1 root root    8 Feb 10 14:13 sbin -> usr/sbin
drwxr-xr-x   2 root root 4096 Feb 10 14:13 srv
dr-xr-xr-x  11 root root    0 Mar  2 02:22 sys
drwxrwxrwt   2 root root 4096 Feb 10 14:21 tmp
drwxr-xr-x  11 root root 4096 Feb 10 14:13 usr
drwxr-xr-x  11 root root 4096 Feb 10 14:21 var

root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:/# ls -a
.   bin   dev  home  lost+found  mnt  proc  run   srv  tmp  var
..  boot  etc  lib   media       opt  root  sbin  sys  usr

root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:/# ls -lh
total 52K
lrwxrwxrwx   1 root root    7 Feb 10 14:13 bin -> usr/bin
drwxr-xr-x   2 root root 4.0K Apr 18  2022 boot
drwxr-xr-x   6 root root 2.7K Mar  2 02:22 dev
drwxr-xr-x  32 root root 4.0K Mar  2 02:22 etc
drwxr-xr-x   2 root root 4.0K Apr 18  2022 home
lrwxrwxrwx   1 root root    7 Feb 10 14:13 lib -> usr/lib
drwx------   2 root root 4.0K Mar  2 01:46 lost+found
drwxr-xr-x   2 root root 4.0K Feb 10 14:13 media
drwxr-xr-x   2 root root 4.0K Feb 10 14:13 mnt
drwxr-xr-x   2 root root 4.0K Feb 10 14:13 opt
dr-xr-xr-x 115 root root    0 Mar  2 02:22 proc
drwx------   2 root root 4.0K Feb 10 14:21 root
drwxr-xr-x   5 root root 4.0K Feb 10 14:22 run
lrwxrwxrwx   1 root root    8 Feb 10 14:13 sbin -> usr/sbin
drwxr-xr-x   2 root root 4.0K Feb 10 14:13 srv
dr-xr-xr-x  11 root root    0 Mar  2 02:22 sys
drwxrwxrwt   2 root root 4.0K Feb 10 14:21 tmp
drwxr-xr-x  11 root root 4.0K Feb 10 14:13 usr
drwxr-xr-x  11 root root 4.0K Feb 10 14:21 var

root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:/# ls -la
total 60
drwxr-xr-x  18 root root 4096 Mar  2 01:46 .
drwxr-xr-x  18 root root 4096 Mar  2 01:46 ..
lrwxrwxrwx   1 root root    7 Feb 10 14:13 bin -> usr/bin
drwxr-xr-x   2 root root 4096 Apr 18  2022 boot
drwxr-xr-x   6 root root 2740 Mar  2 02:22 dev
drwxr-xr-x  32 root root 4096 Mar  2 02:22 etc
drwxr-xr-x   2 root root 4096 Apr 18  2022 home
lrwxrwxrwx   1 root root    7 Feb 10 14:13 lib -> usr/lib
drwx------   2 root root 4096 Mar  2 01:46 lost+found
drwxr-xr-x   2 root root 4096 Feb 10 14:13 media
drwxr-xr-x   2 root root 4096 Feb 10 14:13 mnt
drwxr-xr-x   2 root root 4096 Feb 10 14:13 opt
dr-xr-xr-x 115 root root    0 Mar  2 02:22 proc
drwx------   2 root root 4096 Feb 10 14:21 root
drwxr-xr-x   5 root root 4096 Feb 10 14:22 run
lrwxrwxrwx   1 root root    8 Feb 10 14:13 sbin -> usr/sbin
drwxr-xr-x   2 root root 4096 Feb 10 14:13 srv
dr-xr-xr-x  11 root root    0 Mar  2 02:22 sys
drwxrwxrwt   2 root root 4096 Feb 10 14:21 tmp
drwxr-xr-x  11 root root 4096 Feb 10 14:13 usr
drwxr-xr-x  11 root root 4096 Feb 10 14:21 var
```

1. 절대 경로 vs 상대 경로로 이동

```bash
cd /etc        # 절대경로로 이동
pwd
cd ..          # 상대경로로 상위로
pwd
cd /root       # 다시 root 홈으로

root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:/# cd /etc
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:/etc# pwd
/etc
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:/etc# cd ..
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:/# cd /root
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~#
```

### **2. 파일 조작**

파일 조작 명령어인 `cp`, `mv`, `rm`, `mkdir`, `touch`에 대해 학습한다.

1. 디렉토리 생성: `mkdir`

```bash
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~# cd /root
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~# ls
dream_semester  project
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~# tree
.
|-- dream_semester
`-- project
    `-- backend
        `-- api
```

1. 파일 생성: `touch`

```bash
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~# cd dream_semester/
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# touch hello.txt
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# touch a.txt b.txt c.txt
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# tree
.
|-- a.txt
|-- b.txt
|-- c.txt
`-- hello.txt
```

1. 파일 복사: `cp`

- -r 옵션은 디렉토리 통째로 복사하는 거다.

```bash
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# cp hello.txt hello_copy.txt
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# cp -r /root/dream_semester /tmp/backup
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# ls
a.txt  b.txt  c.txt  hello.txt  hello_copy.txt
```

1. 파일 이동 & 이름 변경: `mv`

```bash
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# mv hello_copy.txt renamed.txt
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# mv renamed.txt /tmp/
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# ls
a.txt  b.txt  c.txt  hello.txt
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# ls /tmp
backup  renamed.txt
```

1. 파일 삭제: `rm`

```bash
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# rm a.txt
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# rm -f b.txt
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# rm -rf /tmp/backup
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# ls
c.txt  hello.txt
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester#
```

### **3. 파일 내용 확인**

1. `cat` - 파일 내용 출력

- Unicode로 들어간다. (복붙시)

```bash
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# cd /root/dream_semester/
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# echo "Hello, Ubuntu!" > hello.txt
echo "\353\221\220\353\262\210\354\247\270 \354\244\204"
>> hello.txt
echo "\354\204\270\353\262\210\354\247\270 \354\244\204"
>> hello.txt
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# cat hello.txt
Hello, Ubuntu!
두번째 줄
세번째 줄
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester#
```

1. `cat`으로 여러 파일 합치기

```bash
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester# echo "\355\214\214\354\23
5\274 A" > a.txt
echo "\355\214\214\354\235\274 B" > b.txt

cat a.txt b.txt          # \353\221\220 \355\214\214\354\235\274 \354
\227\260\354\206\215 \354\266\234\353\240\245
cat a.txt b.txt > c.txt  # \353\221\220 \355\214\214\354\235\274\
354\235\204 \355\225\251\354\263\220\354\204\234 c.txt\35
3\241\234 \354\240\200\354\236\245
cat c.txt
파일 A
파일 B
파일 A
파일 B
root@ed9e41fd-f746-4fe7-856e-d94a8f9568ad:~/dream_semester#
```

1. `less` - 긴 파일을 페이지 단위로 보기

- 여기서부터 docker로 linux image를 받아서 구동시켰다.
  - apple container로 실행시킨 ubuntu 22.04는 매우 light한 버전이라, 패키지 설치되어 있지 않은 것들이 많아 docker로 교체했다.
  - 물론 이것만으로 이유가 될 수는 없는데, apt install less 시 container가 죽어 좀 더 안정화된 docker로 교체했다.
- `less` 패키지는 설치가 되어 있지 않을 텐데, 아래의 명령어로 최신화를 한 뒤 설치해주자.
- `less` 실행 후 조작법
  - `j` 또는 `↓` : 한 줄 아래
  - `k` 또는 `↑` : 한 줄 위
  - `Space` : 한 페이지 아래
  - `q` : 종료

```bash
apt update
apt install less -y

root@ubuntu:/# less /etc/passwd

root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/usr/sbin/nologin
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin
lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin
news:x:9:9:news:/var/spool/news:/usr/sbin/nologin
uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin
proxy:x:13:13:proxy:/bin:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin
list:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin
irc:x:39:39:ircd:/run/ircd:/usr/sbin/nologin
gnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/usr/sbin/nologin
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
_apt:x:100:65534::/nonexistent:/usr/sbin/nologin
/etc/passwd (END)
```

1. cat vs less 차이

```bash
cat /etc/passwd    # 전체 내용을 한번에 출력 (짧은 파일에 적합)
less /etc/passwd   # 페이지 단위로 출력 (긴 파일에 적합)
```

---

## **🔐 권한 관리**

Linux의 권한 관리 방식에 대해 알아본다. 먼저 파일의 권한 체계를 먼저 이해해야된다.

### **1️⃣ 권한 체계 이해**

`ls -l` 을 통해 현재 디렉토리 내 파일에 대한 자세한 정보를 보자.

```bash
root@ubuntu:~/dream_semester# cd /root/dream_semester/
root@ubuntu:~/dream_semester# ls -l
total 0
-rw-r--r-- 1 root root 0 Mar  2 02:55 hello.txt
root@ubuntu:~/dream_semester#
```

여기서 -rw-r… 이런 것들을 볼 수 있는데 이것이 파일의 권한을 의미한다. 좀 더 자세히 확인해보면 아래와 같다.

```bash
- <rw-> <r--> <r-->
│   │     │     │
│   │     │     └── others (다른 사용자) 권한
│   │     └────── group (그룹) 권한
│   └────────── owner (소유자) 권한
└───────────── 파일 타입 (- : 파일, d : 디렉토리)
```

| 문자 | 의미           | 숫자 |
| ---- | -------------- | ---- |
| `r`  | 읽기 (read)    | 4    |
| `w`  | 쓰기 (write)   | 2    |
| `x`  | 실행 (execute) | 1    |
| `-`  | 권한 없음      | 0    |

그럼 이 파일 권한을 변경할 순 없을까? → 당연히 가능하다.

### **2️⃣ chmod — 권한 변경**

- 755 계산법: 7(rwx)=4+2+1, 5(r-x)=4+1, 5(r-x)=4+1

```bash
# 숫자 방식
chmod 755 hello.txt   # rwxr-xr-x
chmod 644 hello.txt   # rw-r--r--
chmod 600 hello.txt   # rw-------

# 확인
ls -l hello.txt
```

### **3️⃣ 실행 권한 실습**

- 스크립트 파일 생성 한 후 권한 주기 이전/이후의 실행 결과 차이를 확인한다.

```bash
root@ubuntu:~/dream_semester# # make script file
root@ubuntu:~/dream_semester# echo '#!/bin/bash' > test.sh
root@ubuntu:~/dream_semester# echo 'echo "Hello, Script!"' >> test.sh
root@ubuntu:~/dream_semester# ./test.sh
bash: ./test.sh: Permission denied
root@ubuntu:~/dream_semester# chmod +x test.sh
root@ubuntu:~/dream_semester# ./test.sh
Hello, Script!
root@ubuntu:~/dream_semester#
```

### **4️⃣ chown — 소유자 변경**

- 새로운 유저를 만들어 hello.txt의 소유자를 새 유저로 변경해보자.
- 이 부분이 지금은 뭐하는 건가 싶지만, 나중에 여러 패키지들을 설치하고 하는 과정에서 설정하는 것이 필요한 순간들이 온다.
  - 간단하게만 이야기를 해보면, 실제 서버 환경에서는 여러 프로세스/서비스가 각각 다른 사용자 권한으로 실행된다.
  - 예를 들어, Docker 컨테이너 안에서 앱을 실행할 대, 보안상 root로 실행하면 위험하고, 다른 사용자를 생성해 해당 사용자 권한으로 앱을 실행한다.
  - 이때, 앱이 읽어야 될 파일들의 소유자를 새로운 사용자로 바꿔줘야 정상 작동한다.
  - 나중에 추가적으로 살펴본다.

```bash
root@ubuntu:~/dream_semester# useradd testuser
root@ubuntu:~/dream_semester# chown testuser hello.txt
root@ubuntu:~/dream_semester# ls -l hello.txt
-rw-r--r-- 1 testuser root 0 Mar  2 02:55 hello.txt
root@ubuntu:~/dream_semester#
```

---

## ✏️ 편집기 & 패키지 관리

### **1️⃣** `vim` 기본 사용법

`apt install vim -y`를 통해 설치를 한다.

| 분류            | 커맨드          | 설명                            |
| --------------- | --------------- | ------------------------------- |
| **모드 전환**   | `i`             | 커서 앞에서 Insert 모드 진입    |
|                 | `a`             | 커서 뒤에서 Insert 모드 진입    |
|                 | `o`             | 아래 새 줄에서 Insert 모드 진입 |
|                 | `O`             | 위 새 줄에서 Insert 모드 진입   |
|                 | `ESC`           | Normal 모드로 복귀              |
| **이동**        | `h` / `l`       | 좌 / 우                         |
|                 | `j` / `k`       | 아래 / 위                       |
|                 | `w`             | 다음 단어로 이동                |
|                 | `b`             | 이전 단어로 이동                |
|                 | `0`             | 줄 맨 앞으로                    |
|                 | `$`             | 줄 맨 끝으로                    |
|                 | `gg`            | 파일 맨 처음으로                |
|                 | `G`             | 파일 맨 끝으로                  |
|                 | `:n`            | n번째 줄로 이동 (예: `:10`)     |
| **편집**        | `dd`            | 현재 줄 삭제                    |
|                 | `yy`            | 현재 줄 복사                    |
|                 | `p`             | 붙여넣기                        |
|                 | `u`             | 실행 취소 (undo)                |
|                 | `Ctrl + r`      | 다시 실행 (redo)                |
|                 | `x`             | 커서 위치 문자 삭제             |
|                 | `dw`            | 커서부터 단어 끝까지 삭제       |
| **검색 & 치환** | `/단어`         | 단어 검색                       |
|                 | `n`             | 다음 검색 결과로                |
|                 | `N`             | 이전 검색 결과로                |
|                 | `:%s/old/new/g` | 파일 전체 old → new 치환        |
| **저장 & 종료** | `:w`            | 저장                            |
|                 | `:q`            | 종료                            |
|                 | `:wq`           | 저장 + 종료                     |
|                 | `:q!`           | 저장 없이 강제 종료             |
|                 | `:w 파일명`     | 다른 이름으로 저장              |

### **2️⃣** `apt` 패키지 관리자

**1] 패키지 목록 업데이트**

```bash
apt update        # 패키지 목록 최신화 (실제 설치 아님)
apt upgrade -y    # 설치된 패키지 전체 업그레이드
```

> `apt update`는 자주 해주는 게 좋다. 새 패키지 설치 전에 항상 먼저 실행하는 습관을 들이자.

**2] 패키지 설치 & 삭제**

```bash
apt install curl -y       # curl 설치
apt install git -y        # git 설치
apt remove curl -y        # 패키지 삭제 (설정 파일 유지)
apt purge curl -y         # 패키지 + 설정 파일까지 완전 삭제
apt autoremove -y         # 불필요한 패키지 자동 정리
```

**3] 패키지 검색 & 정보 확인**

```bash
apt search git            # git 관련 패키지 검색
apt show git              # git 패키지 상세 정보 확인
```

**4] 설치된 패키지 목록 확인**

```bash
dpkg -l                   # 설치된 전체 패키지 목록
dpkg -l | grep git        # git 관련 패키지만 필터링
```

| 커맨드                 | 설명                        |
| ---------------------- | --------------------------- |
| `apt update`           | 패키지 목록 최신화          |
| `apt upgrade`          | 설치된 패키지 업그레이드    |
| `apt install 패키지명` | 패키지 설치                 |
| `apt remove 패키지명`  | 패키지 삭제                 |
| `apt purge 패키지명`   | 패키지 + 설정파일 완전 삭제 |
| `apt autoremove`       | 불필요한 패키지 정리        |
| `apt search 패키지명`  | 패키지 검색                 |
| `apt show 패키지명`    | 패키지 상세 정보            |

---

## ⚙️ 프로세스 & 자동화

### 1️⃣ 프로세스 관리

ps, top, kill 명령어에 대해 학습해본다.

**1] 현재 실행 중인 프로세스 확인**

```bash
ps            # 현재 터미널에서 실행 중인 프로세스
ps aux        # 시스템 전체 프로세스 확인
ps aux | grep bash   # bash 관련 프로세스만 필터링
```

```bash
root@ubuntu:~/dream_semester# ps
  PID TTY          TIME CMD
    1 pts/0    00:00:00 bash
  274 pts/0    00:00:00 ps
root@ubuntu:~/dream_semester# ps aux
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0   4140  2452 pts/0    Ss   02:47   0:00 /bin/bas
root       275  0.0  0.0   6440  2260 pts/0    R+   03:09   0:00 ps aux
root@ubuntu:~/dream_semester# ps aux | grep bash
root         1  0.0  0.0   4140  2452 pts/0    Ss   02:47   0:00 /bin/bash
root@ubuntu:~/dream_semester#
```

**2] 실시간 프로세스 모니터링**

```bash
apt install procps -y   # top 없으면 먼저 설치
top
```

프로세스를 생성해보고, top을 이용해 모니터링 & 조정을 해보자.

- sleep {시간} &을 통해 detached 상황으로 프로세스를 만들어보자.

```bash
root@ubuntu:~/dream_semester# sleep 1000 &
[1] 287
root@ubuntu:~/dream_semester# sleep 2000 &
[2] 288
root@ubuntu:~/dream_semester# sleep 3000 &
[3] 289
root@ubuntu:~/dream_semester# ps aux
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0   4140  2452 pts/0    Ss   05:33   0:00 /bin/bas
root       287  0.0  0.0   2224   888 pts/0    S    06:05   0:00 sleep 10
root       288  0.0  0.0   2224   888 pts/0    S    06:05   0:00 sleep 20
root       289  0.0  0.0   2224   888 pts/0    S    06:05   0:00 sleep 30
root       290  0.0  0.0   6440  2276 pts/0    R+   06:05   0:00 ps aux
root@ubuntu:~/dream_semester#
```

이후 아래의 커맨드를 이용해 process를 kill 해보자. (287번)

> `top` 실행 후 조작법
>
> | 키  | 설명                     |
> | --- | ------------------------ |
> | `q` | 종료                     |
> | `k` | 프로세스 종료 (PID 입력) |
> | `1` | CPU 코어별 사용률 표시   |
> | `M` | 메모리 사용량 순 정렬    |
> | `P` | CPU 사용량 순 정렬       |

```bash
top - 06:08:15 up 37 min,  0 users,  load average: 0.13, 0.03, 0.01
Tasks:   4 total,   1 running,   3 sleeping,   0 stopped,   0 zombie
%Cpu(s):  0.0 us,  0.0 sy,  0.0 ni,100.0 id,  0.0 wa,  0.0 hi,  0.0 si,
MiB Mem :   7837.6 total,   7026.1 free,    397.4 used,    414.2 buff/cac
MiB Swap:   1024.0 total,   1024.0 free,      0.0 used.   7290.1 avail Me

  PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+
  291 root      20   0    6756   2764   2252 R   0.0   0.0   0:00.02
    1 root      20   0    4140   2580   2324 S   0.0   0.0   0:00.21
  288 root      20   0    2224    888    888 S   0.0   0.0   0:00.00
  289 root      20   0    2224    888    888 S   0.0   0.0   0:00.00
```

287번이 사라진다.

**3] 백그라운드 프로세스 & kill**

```bash
# 무한 루프 프로세스 백그라운드로 실행
sleep 1000 &          # & 를 붙이면 백그라운드 실행
ps aux | grep sleep   # PID 확인

kill 프로세스PID       # 프로세스 종료
kill -9 프로세스PID    # 강제 종료
```

### 2️⃣ Bash 스크립트 기초

**1] 변수**

```bash
# 변수 선언 (= 앞뒤 공백 없어야 함)
NAME="성근"
AGE=25

# 변수 사용
echo "이름: $NAME"
echo "나이: $AGE"
```

**2] 조건문**

```bash
NUMBER=10

if [ $NUMBER -gt 5 ]; then
    echo "$NUMBER 는 5보다 크다"
elif [ $NUMBER -eq 5 ]; then
    echo "$NUMBER 는 5와 같다"
else
    echo "$NUMBER 는 5보다 작다"
fi
```

> 비교 연산자 정리
>
> | 연산자 | 설명                |
> | ------ | ------------------- |
> | `-eq`  | 같다 (equal)        |
> | `-ne`  | 다르다 (not equal)  |
> | `-gt`  | 크다 (greater than) |
> | `-lt`  | 작다 (less than)    |
> | `-ge`  | 크거나 같다         |
> | `-le`  | 작거나 같다         |

**3] 반복문**

```bash
# for 반복문
for i in 1 2 3 4 5; do
    echo "현재 숫자: $i"
done

# while 반복문
COUNT=0
while [ $COUNT -lt 5 ]; do
    echo "COUNT: $COUNT"
    COUNT=$((COUNT + 1))
done
```

**4] 함수**

```bash
# 함수 선언
greet() {
    echo "안녕하세요, $1!"   # $1 은 첫번째 인자
}

# 함수 호출
greet "성근"
greet "Ubuntu"
```

**5] 스크립트 파일로 작성**

```bash
vim /root/dream_semester/practice.sh
```

아래 내용을 입력

```bash
#!/bin/bash

NAME="맘편한 이동"
VERSION="1.0.0"

echo "프로젝트: $NAME"
echo "버전: $VERSION"

for i in 1 2 3; do
    echo "$i 번째 실행 중..."
done

echo "완료!"
```

실행해보려면 chmod로 실행권한을 줘야 한다.

```bash
chmod +x /root/dream_semester/practice.sh
./practice.sh
```

**결과**

```bash
root@ubuntu:~/dream_semester# vim /root/dream_semester/practice.sh
root@ubuntu:~/dream_semester# chmod +x /root/dream_semester/practice.sh
root@ubuntu:~/dream_semester# ./practice.sh
프로젝트: 맘편한 이동
버전: 1.0.0
1 번째 실행 중...
2 번째 실행 중...
3 번째 실행 중...
완료!
root@ubuntu:~/dream_semester#
```

---

## 🔑 SSH & 원격 접속

### SSH 키 생성 및 키 기반 인증

**1] SSH 설치**

```bash
apt install openssh-client openssh-server -y
```

**2] SSH 키 생성**

```bash
ssh-keygen -t rsa -b 4096 -C "phd0328@gmail.com"
```

실행하면 3가지를 물어본다.

- 키 저장 위치 → 그냥 Enter (기본값 `~/.ssh/id_rsa` 사용)
- passphrase → 그냥 Enter (비밀번호 없이)
- passphrase 확인 → 그냥 Enter

```bash
root@ubuntu:~/dream_semester# ssh-keygen -t rsa -b 4096 -C "phd0328@gmail.com"
Generating public/private rsa key pair.
Enter file in which to save the key (/root/.ssh/id_rsa):
Created directory '/root/.ssh'.
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /root/.ssh/id_rsa
Your public key has been saved in /root/.ssh/id_rsa.pub
The key fingerprint is:
{FingerPrint} phd0328@gmail.com
The key's randomart image is:
+---[RSA 4096]----+
|      ...        |
|       + ..  .   |
    키 생성된 결과
|    E*.. . .. o  |
+----[SHA256]-----+
```

**3] 생성된 키 확인**

- public, private 키가 생성된 것을 알 수 있다.

```bash
root@ubuntu:~/dream_semester# ls -la ~/.ssh/
total 16
drwx------ 2 root root 4096 Mar  2 06:16 .
drwx------ 1 root root 4096 Mar  2 06:16 ..
-rw------- 1 root root 3381 Mar  2 06:16 id_rsa
-rw-r--r-- 1 root root  743 Mar  2 06:16 id_rsa.pub
```

**4] 키 기반 인증 원리 이해**

**🔄 동작 흐름**

```bash
1. 내가 서버에 접속 시도
        ↓
2. 서버가 authorized_keys에서 공개키 확인
   "어, 이 사람 공개키 등록되어 있네?"
        ↓
3. 서버가 공개키로 암호화된 메시지를 나한테 전송
        ↓
4. 나는 개인키로 그 메시지를 복호화해서 응답
        ↓
5. 서버가 "맞네, 들어와도 돼" → 비밀번호 없이 접속 완료
```

```bash
내 컴퓨터                       원격 서버
─────────                    ─────────
개인키 (id_rsa)    ←→         공개키 (authorized_keys)
(절대 공개 금지)               (서버에 등록)
```

- authrozied_keys는 일종의 약속이다.
  - SSH 서버 프로그램(sshd)는 ‘접속하려는 사용자의 홈 디렉토리 밑’ `.ssh/authrozied_keys` 라는 파일이 있는지 확인하고, 그 안의 키들만 사용하도록 구성되었다.

**5] 공개키 등록**

| **단계**         | **AWS EC2 방식**                                                      | **지금 배우는 수동 방식**                  |
| ---------------- | --------------------------------------------------------------------- | ------------------------------------------ |
| **키 생성**      | AWS 콘솔에서 생성 (AWS가 만들어줌)                                    | 내 컴퓨터에서 `ssh-keygen`으로 직접 생성   |
| **개인키(.pem)** | 내가 다운로드해서 보관                                                | 내 컴퓨터 `~/.ssh/id_rsa`에 보관           |
| **공개키 등록**  | **인스턴스 생성 시 AWS가 자동으로** 서버의 `authorized_keys`에 넣어줌 | 내가 직접 `ssh-copy-id`나 `cat`으로 넣어줌 |

```bash
# authorized_keys 파일에 공개키 등록
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys

# 권한 설정 (이 권한이 안 맞으면 SSH 접속 거부됨)
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/id_rsa
```

---

## 📝 최종 결과물

이번 주에 배운 내용을 활용해 실제로 쓸 수 있는 서버 초기화 스크립트를 작성해보자.

### 1️⃣ `setup.sh` 서버 초기화 스크립트 작성

```bash
root@ubuntu:~/dream_semester# vim setup.sh
root@ubuntu:~/dream_semester# cat setup.sh
#!/bin/bash

echo "Comfortable Move Server setup starts..."

# 1. package list update
echo "[1/5] package update ..."
apt update -y && apt upgrade -y

# 2. Install Python
echo "[2/5] install python..."
apt install python3 python3-pip -y
python3 --version

# 3. Install docker
echo "[3/5] install docker..."
apt install curl -y
curl -fsSL https://get.docker.com | sh
docker --version

# 4. Create Directories
echo "[4/5] create directories..."
mkdir -p /app/backend
mkdir -p /app/logs
mkdir -p /app/data
echo "directory setting ends"
ls /app

# 5. Firewall Setup
echo "[5/5] setup firewall..."."
echo "컨테이너 환경 → 방화벽 설정 스킵"
echo "실제 EC2 서버에서 아래 명령어를 실행할 것"
echo "  ufw allow 22"
echo "  ufw allow 80"
echo "  ufw allow 443"
echo "  ufw allow 8000"
echo "  ufw --force enable"

echo "Comfortable Mover Server setup ends!!"
```

참고로 현재는 docker 컨테이너 환경이라 iptables 접근이 막혀서 ufw가 동작하지 않는다. 호스트의 네트워크 커널을 컨테이너에서 직접 건드릴 수 없기 때문에 나중에 VM을 띄워 활용할 때 사용할 수 있다.
