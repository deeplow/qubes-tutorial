# <p align="center">Qubes Tutorial</p>
<p align="center">Integrated Onboarding Tutorials for Qubes OS.</p>
<br/><br/>

This application's goal is to *guide the user through the most basic concepts and task*, without the needing formal training or documentation reading to get started using the system.

This repository just includes the tutorial engine. The tutorial itself is available [here](https://github.com/deeplow/qubes-onboarding-tutorial).

A video introduction to this project can be seen [at the Qubes mini-summit 2021 (starts at 1h09m52s)](https://youtube.com/watch?v=y3V_V0Vllas)

## Why is this needed?
[Qubes OS](qubes-os.org/) is a security-focused operating system. It's security is based on the principle of "Security Through Isolation". In practice the user has to manage multiple compartments called *qubes*. Each has its own set of applications and is displayed on the same interface. To distinguish them each *qube*'s application is has a user-set border color and name.

This is a fundamentally different way to think about your computer. In reality your are more thinking about mutiple computers. This mental model change causes difficulties in adaptation.

## Documentation
This will be documented soon.


## Development

```bash
dnf install gobject-introspection-devel
```
