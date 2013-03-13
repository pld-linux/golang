# TODO
# - allow disabling tests (currently bcond exists just for showing which are test deps)

# Conditional build:
%bcond_without	tests	# build without tests

Summary:	Go compiler and tools
Name:		golang
Version:	1.0.3
Release:	0.1
License:	BSD
Group:		Development/Languages
URL:		http://golang.org/
Source0:	http://go.googlecode.com/files/go%{version}.src.tar.gz
# Source0-md5:	31acddba58b4592242a3c3c16165866b
BuildRequires:	bison
BuildRequires:	ed
BuildRequires:	mercurial
%if %{with tests}
BuildRequires:	hostname
%endif
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define _enable_debug_packages 0
%define no_install_post_strip 1
%define no_install_post_chrpath 1
%define _noautoreqfiles %{_libdir}/%{name}/src

%define		_vimdatadir	%{_datadir}/vim

%ifarch %{ix86}
%define	GOARCH 386
%endif
%ifarch %{x8664}
%define	GOARCH amd64
%endif

%description
Go is an open source programming environment that makes it easy to
build simple, reliable, and efficient software.

%package -n vim-syntax-%{name}
Summary:	go syntax files for vim
Group:		Applications/Editors
Requires:	%{name} = %{version}-%{release}
Requires:	vim-rt >= 4:7.2.170
%if "%{_rpmversion}" >= "5"
BuildArch:	noarch
%endif

%description -n vim-syntax-%{name}
Go syntax files for vim.

%package -n emacs-%{name}
Summary:	go syntax files for emacs
Group:		Applications/Editors
%if "%{_rpmversion}" >= "5"
BuildArch:	noarch
%endif

%description -n emacs-%{name}
Go mode for Emacs.

%prep
%setup -q -n go

%build
GOSRC=$(pwd)
GOROOT=$(pwd)
GOROOT_FINAL=%{_libdir}/%{name}

GOOS=linux
GOBIN=$GOROOT/bin
GOARCH=%{GOARCH}
export GOARCH GOROOT GOOS GOBIN GOROOT_FINAL
export MAKE="%{__make}"

install -d "$GOBIN"
cd src

LC_ALL=C PATH="$PATH:$GOBIN" ./all.bash

%install
rm -rf $RPM_BUILD_ROOT
GOROOT=$RPM_BUILD_ROOT%{_libdir}/%{name}

install -d $GOROOT/{misc,lib,src}
install -d $RPM_BUILD_ROOT%{_bindir}

cp -a pkg include lib bin $GOROOT
cp -a src/pkg src/cmd $GOROOT/src
cp -a misc/cgo $GOROOT/misc

ln -sf %{_libdir}/%{name}/bin/go $RPM_BUILD_ROOT%{_bindir}/go
ln -sf %{_libdir}/%{name}/bin/godoc $RPM_BUILD_ROOT%{_bindir}/godoc
ln -sf %{_libdir}/%{name}/bin/gofmt $RPM_BUILD_ROOT%{_bindir}/gofmt

ln -sf %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/cgo $RPM_BUILD_ROOT%{_bindir}/cgo
ln -sf %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/ebnflint $RPM_BUILD_ROOT%{_bindir}/ebnflint

%ifarch %{ix86}
tools="8a 8c 8g 8l"
%else
tools="6a 6c 6g 6l"
%endif
for tool in $tools; do
	ln -sf %{_libdir}/%{name}/pkg/tool/linux_%{GOARCH}/$tool $RPM_BUILD_ROOT%{_bindir}/$tool
done

install -d $RPM_BUILD_ROOT%{_datadir}/emacs/site-lisp
cp -p misc/emacs/go*.el $RPM_BUILD_ROOT%{_datadir}/emacs/site-lisp/

VIMFILES="syntax/go.vim ftdetect/gofiletype.vim ftplugin/go/fmt.vim ftplugin/go/import.vim indent/go.vim"
for i in $VIMFILES; do
	install -Dp misc/vim/$i $RPM_BUILD_ROOT%{_vindatadir}/$i
done

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%doc AUTHORS CONTRIBUTORS LICENSE README doc/*
%attr(755,root,root) %{_bindir}/*
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

%files -n vim-syntax-%{name}
%defattr(644,root,root,755)
%{_vindatadir}/ftdetect/gofiletype.vim
%{_vindatadir}/ftplugin/go
%{_vindatadir}/indent/go.vim
%{_vindatadir}/syntax/go.vim

%files -n emacs-%{name}
%defattr(644,root,root,755)
%{_datadir}/emacs/site-lisp/go-mode*.el
