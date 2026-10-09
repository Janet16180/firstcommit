"use strict";

/*
 * The field guide's words in English, as GuideCard and GuidePictures receive them once localized
 * (GuideText.card and GuideText.pictures, with each place's label): one copy for every guide test.
 */

const pictures = {
  places: { folder: "Working folder (workshop)", staging: "Staging area (cargo dock)", vault: "Repository (vault)", remote: "Remote (mothership)" },
  notYet: "not there yet",
  empty: "empty",
  head: "HEAD, you are here",
  states: { new: "new", edited: "edited", conflict: "conflict", clean: "saved" },
  ghost: "no name leads here",
  notYours: "on the mothership only",
  by: { you: "your commit", alex: "Alex's commit" },
  marks: { merge: "merge commit", revert: "undoes the one below" },
  gone: "taken off",
  left: "left the folder",
  mothership: "mothership",
  notes: { notInMain: "not in main", notShown: "not shown", unchanged: "unchanged" },
};

const card = {
  before: "Before",
  after: "After",
  onlyLooks: "Nothing changes: it only looks.",
  prints: "What git prints",
  silent: "(prints nothing)",
  mistake: "Common mistake",
  taught: "Where you learn it",
  related: "Related",
  conflict: "See a conflict, step by step",
  chainKey: "HEAD marks where you are; a dashed name is your bookmark of the mothership.",
  showAll: "Show all {count} lines",
  showLess: "Show fewer lines",
  tryIt: "Try it in the playground",
  changed: "Changed",
  same: "Same",
  or: "or",
};

module.exports = { pictures, card };
