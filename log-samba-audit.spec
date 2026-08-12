%define sname log-samba-audit
Name:          log-samba-audit-viewer
Version:       1.0
Release:       alt1.gita0f0070
License:       %gpl3only
Group:         System/Configuration/Other
Source:        %name-v%version.tgz
BuildArch:     noarch

Summary:       Samba AD JSON audit log viewer
Url:           https://github.com/x09/log-samba-audit

BuildRequires: 	rpm-build-licenses

Requires: 	python3-modules-tkinter
Requires:	python3-module-lark >= 1.1
Requires: 	python3

%add_python3_path %_datadir/%name

%description
log-samba-audit-viewer is a GUI tool for viewing and searching Samba Active Directory
JSON audit logs via systemd-journal-gatewayd. Supports real-time following,
date-range and text filtering, backward journal scanning, and displays KDC/auth
events with colored status indicators.

%prep
%setup -n %sname-v%version

%install
mkdir -p %buildroot%_datadir/%name
mkdir -p %buildroot%_bindir
mkdir -p %buildroot%_desktopdir

mkdir -p %buildroot%_datadir/%name/icons/
cp icons/act*.png %buildroot%_datadir/%name/icons/

cp -a lsa %buildroot%_datadir/%{name}/
cp log-samba-audit-viewer.py %{buildroot}%_bindir/log-samba-audit-viewer

for language in ru; do
	mkdir -p %buildroot%_datadir/locale/$language/LC_MESSAGES
	install -m644 locale/$language/LC_MESSAGES/log-samba-audit.mo %buildroot/%_datadir/locale/$language/LC_MESSAGES/
done

cp %name.desktop %buildroot/%_desktopdir/%name.desktop

for s in 32 64 128 256; do
    mkdir -p %buildroot/%_iconsdir/hicolor/${s}x${s}/apps/
    cp icons/%sname-${s}.png %buildroot/%_iconsdir/hicolor/${s}x${s}/apps/%name.png
done



mkdir -p %buildroot/%_bindir/
cp %name.py %buildroot/%_bindir/log-samba-audit-viewer
chmod 755 %buildroot/%_bindir/log-samba-audit-viewer

%post

%postun

%files
%doc README.md SEARCH_SYNTAX.md
%_bindir/log-samba-audit-viewer
%_iconsdir/hicolor/*
%_desktopdir/%name.desktop
%_datadir/%name/lsa/*
%_datadir/%name/icons/act-*.png
%_datadir/locale/ru/LC_MESSAGES/log-samba-audit.mo


%changelog
* Wed Aug 12 2026 Anton Shevtsov <shevtsov.anton@gmail.com> 1.0-alt1.gita0f0070
- Add support for search logical expressions (using the python3-module-lark)

* Tue Aug 11 2026 Anton Shevtsov <shevtsov.anton@gmail.com> 1.0-alt1.git6649950
- New build

* Tue Aug 11 2026 Anton Shevtsov <shevtsov.anton@gmail.com> 1.0-alt1.git5718ecd
- New build

* Wed Aug 05 2026 Anton Shevtsov <shevtsov.anton@gmail.com> 1.0-alt1
- First version
