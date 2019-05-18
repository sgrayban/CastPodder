# CastPodder Spec
# $Id: CastPodder.spec 148 2006-11-07 08:18:34Z sgrayban $

%define		name CastPodder
%define		version 5.5
%define		release 1.0%{_my_ext}
%define		__libtoolize /bin/true
%define		__cputoolize /bin/true


Name:           %{name}
Version:        %{version}
Release:        %{release}
Summary:        CastPodder is a Media Aggregator
Vendor:         %{vendor}
Packager:       %{packager}
Distribution:   %{distribution}
License:        Commercial
URL:            http://forum.castpodder.net/index.php?ind=downloads
Group:          Networking/News
Source:         %{name}-%{version}.tar.bz2
Source1:        %{name}-16.png
Source2:        %{name}-32.png
Source3:        %{name}-48.png
BuildRoot:      %{_tmppath}/%{name}-buildroot
BuildArch:      noarch
Requires:       wxPythonGTK
Requires:       pyxmms pythonlib libxml2-python
Obsoletes:	iPodder %{name}

%description
CastPodder is technically a "Media Aggregator,"
a program that allows you to select and download audio
files from anywhere on the Internet to your desktop.

CastPodder makes the process easy by helping you select audio files
from among the thousands of audio sources on the web and downloading
those files to your computer. Once you select a feed or location,
it will download those files automatically at times you specify
and have the files waiting for you on your computer,
so you don't have to spend a lot of time manually selecting and waiting
for downloads. You can play your selected audio files using iTunes
or other "jukebox" software, or load them on to your iPod or other
portable digital media player to play anytime you want.

%prep
rm -rf %buildroot

%setup -q -n castpodder
%build



%install

# remove all SVN files so that they don't get "accidently" installed
for SVNDIR in `find . -type d -name .svn` ; do
    /bin/rm -rf $SVNDIR
done

mkdir -p %buildroot/%_bindir
mkdir -p %buildroot/%_datadir/%{name}
mkdir -p %buildroot/opt/%{name}
cp -f -R * %buildroot/opt/%{name}
cp -f %buildroot/opt/%{name}/%{name}.sh $RPM_BUILD_ROOT/%_bindir/%{name}
chmod -R 755 %buildroot/opt/%{name}/*.py

#menus
install -d %buildroot/%{_menudir}
cat <<EOF >%buildroot/%{_menudir}/%{name}
?package(%{name}):command="%{_bindir}/%{name}" \
                  icon=%{name}.png \
                  needs="x11" \
                  section="Networking/News" \
                  title="CastPodder"\
                  longtitle="%{summary}"
EOF

install -m644 %{SOURCE1} -D %buildroot/%{_miconsdir}/%{name}.png
install -m644 %{SOURCE2} -D %buildroot/%{_iconsdir}/%{name}.png
install -m644 %{SOURCE3} -D %buildroot/%{_liconsdir}/%{name}.png

%clean
rm -rf %buildroot

%files
%defattr(-,root,root)
%doc README NOTES ChangeLog TODO KNOWN-ISSUES docs THANKS INSTALL AUTHORS Software_License_Agreement.html Software_License_Agreement.txt
%attr(0755,root,root) %{_bindir}/%{name}
%_menudir/%{name}
%_iconsdir/%{name}.png
%_liconsdir/%{name}.png
%_miconsdir/%{name}.png
/opt/%{name}/*

%pre
# lets make sure nothing is there so we delete the old
# directory first before installing - sgrayban
rm -fr /opt/%{name}

%post
%{update_menus}

%postun
%{clean_menus}


%changelog

* Mon Jul 24 2006 Scott Grayban <sgrayban@mandriva.org> 5.1
  - New version release from the CastPodder Team

* Sat Apr 01 2006 Scott Grayban <sgrayban@castpodder.net> 5.0
  - New version release from the CastPodder Team

* Sat Nov 19 2005 Scott Grayban <sgrayban@castpodder.net> 3.2
  - New version release from the CastPodder Team

* Sat Nov 12 2005 Scott Grayban <sgrayban@castpodder.net> 3.1
  - New version release from the CastPodder Team

* Fri Oct 7 2005 Scott Grayban <sgrayban@borgnet.us> 3.0
  - New version release from the CastPodder Team
