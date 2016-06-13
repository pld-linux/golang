# TODO
# - allow disabling tests (currently bcond exists just for showing which are test deps)
# - add verbose build output (currently dummy bcond)
# - setup GOMAXPROCS=2 from _smp_mflags
# - fix CC containing spaces (ccache)
# - check if hg use at build time can be dropped
# - build all target archs, subpackage them: http://golang.org/doc/install/source#environment
# - subpackage -src files?
# - subpackage for "shared"?

# Conditional build:
%bcond_without	verbose		# verbose build (V=1)
%bcond_without	tests		# build without tests [nop actually]
%bcond_without	shared		# Build golang shared objects for stdlib
%bcond_without	ext_linker	# Build golang using external/internal(close to cgo disabled) linking.
%bcond_without	cgo

%ifnarch %{ix86} %{x8664} %{arm} ppc64le aarch64
%undefine	with_shared
%undefine	with_ext_linker
%undefine	with_cgo
%endif

Summary:	Go compiler and tools
Summary(pl.UTF-8):	Kompilator języka Go i narzędzia
Name:		golang
Version:	1.6.2
Release:	1
# source tree includes several copies of Mark.Twain-Tom.Sawyer.txt under Public Domain
License:	BSD and Public Domain
Group:		Development/Languages
# Source0Download: https://golang.org/dl/
Source0:	https://storage.googleapis.com/golang/go%{version}.src.tar.gz
# Source0-md5:	d1b50fa98d9a71eeee829051411e6207
Patch0:		ca-certs.patch
Patch1:		%{name}-binutils.patch
Patch2:		%{name}-1.2-verbose-build.patch
Patch4:		go1.5beta1-disable-TestGdbPython.patch
Patch5:		go1.5-zoneinfo_testing_only.patch
URL:		http://golang.org/
BuildRequires:	bash
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
BuildRequires:	tzdata
%endif
Requires:	ca-certificates
Conflicts:	gcc-go
ExclusiveArch:	%{ix86} %{x8664} %{arm}
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

%description
Go is an open source programming environment that makes it easy to
build simple, reliable, and efficient software.

%description -l pl.UTF-8
Go to mające otwarte źródła środowisko do programowania, pozwalające
na łatwe tworzenie prostych, pewnych i wydajnych programów.

%package shared
Summary:	Golang shared object libraries
Group:		Libraries
Requires:	%{name} = %{version}-%{release}

%description shared
Golang shared object libraries

%package doc
Summary:	Manual for go
Summary(fr.UTF-8):	Documentation pour go
Summary(it.UTF-8):	Documentazione di go
Summary(pl.UTF-8):	Podręcznik dla go
Group:		Documentation
%if "%{_rpmversion}" >= "5"
BuildArch:	noarch
%endif

%description doc
Documentation for go.

%description doc -l fr.UTF-8
Documentation pour go.

%description doc -l it.UTF-8
Documentazione di go.

%description doc -l pl.UTF-8
Dokumentacja do go.

%prep
%setup -qc
mv go/* .
%patch0 -p1
#%patch1 -p1 seems outdated, compiler rewritten in .go instead of .c
%patch2 -p1
%patch4 -p1
%patch5 -p1

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
%if %{without external_linker}
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
ln -sf %{_libdir}/%{name}/bin/godoc $RPM_BUILD_ROOT%{_bindir}/godoc
ln -sf %{_libdir}/%{name}/bin/gofmt $RPM_BUILD_ROOT%{_bindir}/gofmt

ln -sf %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/cgo $RPM_BUILD_ROOT%{_bindir}/cgo
ln -sf %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/ebnflint $RPM_BUILD_ROOT%{_bindir}/ebnflint

%ifarch %{ix86}
tools="8a 8c 8g 8l"
%endif
%ifarch %{x8664}
tools="6a 6c 6g 6l"
%endif
%ifarch %{arm}
tools="5a 5c 5g 5l"
%endif
for tool in $tools; do
	ln -sf %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/$tool $RPM_BUILD_ROOT%{_bindir}/$tool
done

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%doc AUTHORS CONTRIBUTORS LICENSE
%ifarch %{arm}
%attr(755,root,root) %{_bindir}/5a
%attr(755,root,root) %{_bindir}/5c
%attr(755,root,root) %{_bindir}/5g
%attr(755,root,root) %{_bindir}/5l
%endif
%ifarch %{x8664}
%attr(755,root,root) %{_bindir}/6a
%attr(755,root,root) %{_bindir}/6c
%attr(755,root,root) %{_bindir}/6g
%attr(755,root,root) %{_bindir}/6l
%endif
%ifarch %{ix86}
%attr(755,root,root) %{_bindir}/8a
%attr(755,root,root) %{_bindir}/8c
%attr(755,root,root) %{_bindir}/8g
%attr(755,root,root) %{_bindir}/8l
%endif
%attr(755,root,root) %{_bindir}/cgo
%attr(755,root,root) %{_bindir}/ebnflint
%attr(755,root,root) %{_bindir}/go
%attr(755,root,root) %{_bindir}/godoc
%attr(755,root,root) %{_bindir}/gofmt
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/VERSION
%dir %{_libdir}/%{name}/bin
%attr(755,root,root) %{_libdir}/%{name}/bin/*

%{_libdir}/%{name}/lib
%{_libdir}/%{name}/misc
%{_libdir}/%{name}/src
%dir %{_libdir}/%{name}/pkg
%{_libdir}/%{name}/pkg/linux_%{GOARCH}
%{_libdir}/%{name}/pkg/obj
%dir %{_libdir}/%{name}/pkg/tool
%dir %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/*

%{_libdir}/%{name}/pkg/bootstrap
%{_libdir}/%{name}/pkg/include

%if 0
#ifarch %{x8664}
%dir %{_libdir}/%{name}/pkg/linux_%{GOARCH}_race
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/*.a
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/compress
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/container
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/crypto
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/debug
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/encoding
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/go
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/hash
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/internal
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/io
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/math
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/mime
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/net
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/os
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/path
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/regexp
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/runtime
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/sync
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/text
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_race/unicode
%endif

%if %{with shared}
%files shared
%defattr(644,root,root,755)
%{_libdir}/%{name}/pkg/linux_%{GOARCH}_dynlink
%endif

%files doc
%defattr(644,root,root,755)
%doc doc/*
