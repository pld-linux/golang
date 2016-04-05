# TODO
# - allow disabling tests (currently bcond exists just for showing which are test deps)
# - add verbose build output (currently dummy bcond)
# - setup GOMAXPROCS=2 from _smp_mflags
# - fix CC containing spaces (ccache)
# - check if hg use at build time can be dropped
# - build all target archs, subpackage them: http://golang.org/doc/install/source#environment
# - subpackage -src files?

# Conditional build:
%bcond_without	tests	# build without tests [nop actually]
%bcond_without	verbose	# verbose build (V=1)
%bcond_with	emacs	# Go mode for Emacs
%bcond_with	vim	# Go syntax files for Vim

Summary:	Go compiler and tools
Summary(pl.UTF-8):	Kompilator języka Go i narzędzia
Name:		golang
Version:	1.4.3
Release:	1
License:	BSD
Group:		Development/Languages
# Source0Download: https://golang.org/dl/
Source0:	https://storage.googleapis.com/golang/go%{version}.src.tar.gz
# Source0-md5:	dfb604511115dd402a77a553a5923a04
Patch0:		ca-certs.patch
Patch1:		%{name}-binutils.patch
URL:		http://golang.org/
BuildRequires:	bash
BuildRequires:	rpm-pythonprov
%if %{with tests}
BuildRequires:	hostname
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

%ifarch %{ix86}
%define	GOARCH 386
%endif
%ifarch %{x8664}
%define	GOARCH amd64
%endif

%define		_vimdatadir	%{_datadir}/vim

%description
Go is an open source programming environment that makes it easy to
build simple, reliable, and efficient software.

%description -l pl.UTF-8
Go to mające otwarte źródła środowisko do programowania, pozwalające
na łatwe tworzenie prostych, pewnych i wydajnych programów.

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

%package -n vim-syntax-%{name}
Summary:	Go syntax files for Vim
Summary(pl.UTF-8):	Pliki składni Go dla Vima
Group:		Applications/Editors
Requires:	vim-rt >= 4:7.2.170
%if "%{_rpmversion}" >= "5"
BuildArch:	noarch
%endif

%description -n vim-syntax-%{name}
Go syntax files for vim.

%description -n vim-syntax-%{name} -l pl.UTF-8
Pliki składni Go dla Vima.

%package -n emacs-%{name}
Summary:	Go mode for Emacs
Summary(pl.UTF-8):	Tryb Go dla Emacsa
Group:		Applications/Editors
%if "%{_rpmversion}" >= "5"
BuildArch:	noarch
%endif

%description -n emacs-%{name}
Go mode for Emacs.

%description -n emacs-%{name} -l pl.UTF-8
Tryb Go dla Emacsa.

%prep
%setup -qc
mv go/* .
%patch0 -p1
%patch1 -p1

cat > env.sh <<'EOF'
export GOROOT=$(pwd)
export GOROOT_FINAL=%{_libdir}/%{name}

export GOOS=linux
export GOBIN=$GOROOT/bin
export GOARCH=%{GOARCH}
export GOROOT_FINAL
export MAKE="%{__make}"
CC="%{__cc}"
export CC="${CC#ccache }"

export PATH="$PATH:$GOBIN"
EOF

install -d bin

# optflags for go tools build
nflags="\"$(echo '%{rpmcflags}' | sed -e 's/^[ 	]*//;s/[ 	]*$//;s/[ 	]\+/ /g' -e 's/ /\",\"/g')\""
%{__sed} -i -e "s/\"-O2\"/$nflags/" src/cmd/dist/build.c
# NOTE: optflags used in gcc calls from go compiler are in src/cmd/go/build.go

%build
. ./env.sh

cd src
./all.bash

%install
rm -rf $RPM_BUILD_ROOT
GOROOT=$RPM_BUILD_ROOT%{_libdir}/%{name}

install -d $GOROOT/{misc,lib,src}
install -d $RPM_BUILD_ROOT%{_bindir}

cp -a pkg include lib bin src $GOROOT
cp -a misc/cgo $GOROOT/misc
# kill Win32 and Plan9 scripts
find $GOROOT -name '*.bat' -o -name '*.rc' | xargs %{__rm}

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

%if %{with emacs}
install -d $RPM_BUILD_ROOT%{_datadir}/emacs/site-lisp
cp -p misc/emacs/go*.el $RPM_BUILD_ROOT%{_datadir}/emacs/site-lisp/
%endif

%if %{with vim}
VIMFILES="syntax/go.vim ftdetect/gofiletype.vim ftplugin/go/fmt.vim ftplugin/go/import.vim indent/go.vim"
for i in $VIMFILES; do
	install -Dp misc/vim/$i $RPM_BUILD_ROOT%{_vimdatadir}/$i
done
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%doc AUTHORS CONTRIBUTORS LICENSE README
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
%dir %{_libdir}/%{name}/bin
%attr(755,root,root) %{_libdir}/%{name}/bin/*

%{_libdir}/%{name}/include
%{_libdir}/%{name}/lib
%{_libdir}/%{name}/misc
%{_libdir}/%{name}/src
%dir %{_libdir}/%{name}/pkg
%{_libdir}/%{name}/pkg/linux_%{GOARCH}
%{_libdir}/%{name}/pkg/obj
%dir %{_libdir}/%{name}/pkg/tool
%dir %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}
%attr(755,root,root) %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/*

%ifarch %{x8664}
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

%files doc
%defattr(644,root,root,755)
%doc doc/*

%if %{with vim}
%files -n vim-syntax-%{name}
%defattr(644,root,root,755)
%{_vimdatadir}/ftdetect/gofiletype.vim
%{_vimdatadir}/ftplugin/go
%{_vimdatadir}/indent/go.vim
%{_vimdatadir}/syntax/go.vim
%endif

%if %{with emacs}
%files -n emacs-%{name}
%defattr(644,root,root,755)
%{_datadir}/emacs/site-lisp/go-mode*.el
%endif
