# NOTE: build needs >128 processes limit
# TODO
# - allow disabling tests (currently bcond exists just for showing which are test deps)
# - add verbose build output (currently dummy bcond)
# - setup GOMAXPROCS=2 from _smp_mflags
# - fix CC containing spaces (ccache)
# - check if hg use at build time can be dropped
# - build all target archs, subpackage them: http://golang.org/doc/install/source#environment
#   or choose only useful crosscompilers?
# - subpackage -src files?

# Conditional build:
%bcond_without	verbose		# verbose build (V=1)
%bcond_without	tests		# build without tests [nop actually]
%bcond_without	shared		# Build golang shared objects for stdlib
%bcond_without	ext_linker	# Build golang using external/internal (close to cgo disabled) linking
%bcond_without	cgo		# cgo (importing C libraries) support
%bcond_with	bootstrap	# bootstrap build

%ifnarch %{ix86} %{x8664} %{arm} aarch64 mips64 mips64le ppc64le
%undefine	with_shared
%undefine	with_ext_linker
%undefine	with_cgo
%endif

Summary:	Go compiler and tools
Summary(pl.UTF-8):	Kompilator języka Go i narzędzia
Name:		golang
Version:	1.17.7
Release:	1
# source tree includes several copies of Mark.Twain-Tom.Sawyer.txt under Public Domain
License:	BSD and Public Domain
Group:		Development/Languages
# Source0Download: https://golang.org/dl/
Source0:	https://storage.googleapis.com/golang/go%{version}.src.tar.gz
# Source0-md5:	063999612df20d2f9b5777fb60eb2f82
Patch0:		ca-certs.patch
Patch1:		0001-Don-t-use-the-bundled-tzdata-at-runtime-except-for-t.patch
URL:		https://golang.org/
BuildRequires:	bash
BuildRequires:	rpm-build >= 4.6
BuildRequires:	rpm-pythonprov
# The compiler is written in Go. Needs go(1.4+) compiler for build.
%if %{with bootstrap}
BuildRequires:	gcc-go >= 6:5
%else
BuildRequires:	golang >= 1.4
%endif
%if %{with tests}
BuildRequires:	glibc-static
BuildRequires:	hostname
BuildRequires:	pcre-devel
BuildRequires:	rpmbuild(macros) >= 2.007
BuildRequires:	tzdata
%endif
Requires:	ca-certificates
Conflicts:	gcc-go
ExclusiveArch:	%{ix86} %{x8664} %{armv5} %{armv6} %{armv7} aarch64 mips mipsel mips64 mips64el ppc64 ppc64le riscv64 s390x
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		no_install_post_strip	1
%define		no_install_post_chrpath	1
%define		_enable_debug_packages	0
%define		_noautoreqfiles		%{_libdir}/%{name}/src

%define	goroot %{_libdir}/%{name}

%ifarch %{ix86}
%define	GOARCH 386
%endif
%ifarch %{x8664}
%define	GOARCH amd64
%endif
%ifarch %{armv5}
%define	GOARCH arm
%define	GOARM 5
%endif
%ifarch %{armv6}
%define	GOARCH arm
%define	GOARM 6
%endif
%ifarch %{armv7}
%define	GOARCH arm
%define	GOARM 7
%endif
%ifarch aarch64
%define	GOARCH arm64
%endif
%ifarch mipsel
%define	GOARCH mipsle
%endif
%ifarch mips64el
%define	GOARCH mips64le
%endif
%ifarch mips mips64 ppc64 ppc64le riscv64 s390x
%define	GOARCH %{_arch}
%endif

%description
Go is an open source programming environment that makes it easy to
build simple, reliable, and efficient software.

%description -l pl.UTF-8
Go to mające otwarte źródła środowisko do programowania, pozwalające
na łatwe tworzenie prostych, pewnych i wydajnych programów.

%package shared
Summary:	Golang shared object libraries
Summary(pl.UTF-8):	Biblioteki obiektów współdzielonych dla języka Go
Group:		Libraries
Requires:	%{name} = %{version}-%{release}

%description shared
Golang shared object libraries.

%description shared -l pl.UTF-8
Biblioteki obiektów współdzielonych dla języka Go.

%package doc
Summary:	Documentation for Go language
Summary(fr.UTF-8):	Documentation pour Go
Summary(it.UTF-8):	Documentazione di Go
Summary(pl.UTF-8):	Dokumentacja do języka Go
Group:		Documentation
BuildArch:	noarch

%description doc
Documentation for Go language.

%description doc -l fr.UTF-8
Documentation pour Go.

%description doc -l it.UTF-8
Documentazione di Go.

%description doc -l pl.UTF-8
Dokumentacja do języka Go.

%prep
%setup -qc
%{__mv} go/* .
%patch0 -p1
%patch1 -p1

# clean patch backups
find . -name '*.orig' | xargs -r %{__rm}

cat > env.sh <<'EOF'
# bootstrap compiler GOROOT
%if %{with bootstrap}
export GOROOT_BOOTSTRAP=%{_prefix}
%else
export GOROOT_BOOTSTRAP=%{goroot}
%endif
export GOROOT_FINAL=%{goroot}

export GOHOSTOS=linux
export GOHOSTARCH=%{GOARCH}

export GOOS=linux
export GOARCH=%{GOARCH}
%{?GOARM:export GOARM=%{GOARM}}
%if %{without ext_linker}
export GO_LDFLAGS="-linkmode internal"
%endif
%if %{with cgo}
export CGO_ENABLED=1
%else
export CGO_ENABLED=0
%endif

# use our gcc options for this build, but store gcc as default for compiler
export CFLAGS="%{rpmcflags}"
export LDFLAGS="%{rpmldflags}"

CC="%{__cc}"
export CC="${CC#ccache }"
export CC_FOR_TARGET="$CC"
EOF

grep -rl '#!.*env bash' . | xargs %{__sed} -i -e '1{
	s,^#!.*bin/env bash,#!%{__bash},
}'

%if 0
# optflags for go tools build
nflags="\"$(echo '%{rpmcflags}' | sed -e 's/^[ 	]*//;s/[ 	]*$//;s/[ 	]\+/ /g' -e 's/ /\",\"/g')\""
%{__sed} -i -e "s/\"-O2\"/$nflags/" src/cmd/dist/build.c
# NOTE: optflags used in gcc calls from go compiler are in src/cmd/go/build.go
%endif

%build
. ./env.sh
cd src
./make.bash --no-clean
cd ..

# build shared std lib
%if %{with shared}
GOROOT=$(pwd) PATH=$(pwd)/bin:$PATH go install -buildmode=shared std
%endif

%install
rm -rf $RPM_BUILD_ROOT
GOROOT=$RPM_BUILD_ROOT%{goroot}

install -d $GOROOT/{misc,lib,src}
install -d $RPM_BUILD_ROOT%{_bindir}

cp -a pkg lib bin src VERSION $GOROOT
cp -a misc/cgo $GOROOT/misc

# kill Win32 and Plan9 scripts
find $GOROOT -name '*.bat' -o -name '*.rc' | xargs %{__rm}

# https://github.com/golang/go/issues/4749
find $GOROOT/src | xargs touch -r $GOROOT/VERSION
# and level out all the built archives
touch $GOROOT/pkg
find $GOROOT/pkg | xargs touch -r $GOROOT/pkg

ln -sf %{_libdir}/%{name}/bin/go $RPM_BUILD_ROOT%{_bindir}/go
ln -sf %{_libdir}/%{name}/bin/gofmt $RPM_BUILD_ROOT%{_bindir}/gofmt
ln -sf %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/cgo $RPM_BUILD_ROOT%{_bindir}/cgo

# FIXME: do we need whole sources, including build scripts?
# for now, remove only non-Linux stuff
%{__rm} \
	$RPM_BUILD_ROOT%{_libdir}/%{name}/src/syscall/{mksyscall,mksysctl_openbsd,mksysnum_{dragonfly,freebsd,netbsd,openbsd}}.pl
# ...and tests
%{__rm} -r $RPM_BUILD_ROOT%{_libdir}/%{name}/src/internal/trace \
	   $RPM_BUILD_ROOT%{_libdir}/%{name}/misc/cgo/{errors,fortran,test*}
find $RPM_BUILD_ROOT%{_libdir}/%{name} -name testdata -prune | xargs %{__rm} -r

# unenvize remaining scripts
%{__sed} -i -e '1s,/usr/bin/env bash,/bin/bash,' $RPM_BUILD_ROOT%{_libdir}/%{name}/src/*.bash
%{__sed} -i -e '1s,/usr/bin/env bash,/bin/bash,' $RPM_BUILD_ROOT%{_libdir}/%{name}/src/syscall/*.sh
%{__sed} -i -e '1s,/usr/bin/env bash,/bin/bash,' $RPM_BUILD_ROOT%{_libdir}/%{name}/src/cmd/vendor/golang.org/x/sys/unix/*.sh
%{__sed} -i -e '1s,/usr/bin/env bash,/bin/bash,' $RPM_BUILD_ROOT%{_libdir}/%{name}/src/cmd/go/*.sh
%{__sed} -i -e '1s,/usr/bin/env perl,/usr/bin/perl,' $RPM_BUILD_ROOT%{_libdir}/%{name}/src/syscall/*.pl

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%doc AUTHORS CONTRIBUTORS LICENSE
%attr(755,root,root) %{_bindir}/cgo
%attr(755,root,root) %{_bindir}/go
%attr(755,root,root) %{_bindir}/gofmt
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/VERSION
%dir %{_libdir}/%{name}/bin
%attr(755,root,root) %{_libdir}/%{name}/bin/go
%attr(755,root,root) %{_libdir}/%{name}/bin/gofmt

%{_libdir}/%{name}/lib
%{_libdir}/%{name}/misc
%{_libdir}/%{name}/src
%dir %{_libdir}/%{name}/pkg
%{_libdir}/%{name}/pkg/linux_%{GOARCH}
%{_libdir}/%{name}/pkg/obj
%dir %{_libdir}/%{name}/pkg/tool
%dir %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/addr2line
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/api
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/asm
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/buildid
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/cgo
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/compile
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/cover
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/dist
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/doc
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/fix
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/link
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/nm
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/objdump
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/pack
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/pprof
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/test2json
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/trace
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/vet

%{_libdir}/%{name}/pkg/include

%if %{with shared}
%files shared
%defattr(644,root,root,755)
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_dynlink
%endif

%files doc
%defattr(644,root,root,755)
%doc doc/*
