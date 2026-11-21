import { L, LL, P, PL, T, S, write, ghosts, sleep, clickText } from "./lib.mjs";
write("a-firstrun", [
  { name: "a01-home-laptop-dark", url: "/#/", ...L, js: `return {ghosts: ${ghosts}, sw: document.documentElement.scrollHeight, nav: [document.querySelector('.nav').scrollWidth, document.querySelector('.nav').clientWidth]};` },
  { name: "a02-home-laptop-dark-s2", url: "/#/", ...L, js: "window.scrollTo(0, 700);" },
  { name: "a03-home-laptop-dark-bottom", url: "/#/", ...L, js: "window.scrollTo(0, 99999);" },
  { name: "a04-home-laptop-light", url: "/#/", ...LL },
  { name: "a05-home-laptop-light-s2", url: "/#/", ...LL, js: "window.scrollTo(0, 620);" },
  { name: "a06-home-phone-dark", url: "/#/", ...P, js: `return {ghosts: ${ghosts}, nav: [document.querySelector('.nav').scrollWidth, document.querySelector('.nav').clientWidth], h: document.documentElement.scrollHeight};` },
  { name: "a07-home-phone-dark-s2", url: "/#/", ...P, js: "window.scrollTo(0, 800);" },
  { name: "a08-home-phone-dark-s3", url: "/#/", ...P, js: "window.scrollTo(0, 1600);" },
  { name: "a09-home-phone-dark-bottom", url: "/#/", ...P, js: "window.scrollTo(0, 99999);" },
  { name: "a10-home-phone-light", url: "/#/", ...PL },
  { name: "a11-home-tablet-light", url: "/#/", ...T },
  { name: "a12-home-short-dark", url: "/#/", ...S },
]);
