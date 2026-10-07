"use strict";

/*
 * Reading the lines typed in the game's terminal (Observation.commands: {line, status}). It only
 * splits a line into its shell commands and names their git subcommands; it never runs or
 * imitates them. Defines one global, Typed.
 *
 * gitCommands(lines) names the git subcommands of the lines that succeeded, in order ("add",
 * "commit", ...). Whether a chained line's single commands each succeeded is not known, so a
 * line that ended well counts whole.
 */

/* exported Typed */

const Typed = (function () {
  /* A shell operator, a comment, or a word (quotes and backslash escapes kept inside it). */
  const TOKENS = /(&&|\|\||[;&|\n])|#.*|((?:[^\s'"\\;&|]|\\.|'[^']*'|"(?:[^"\\]|\\.)*")+)/g;
  const unquote = (word) => word.replace(/'([^']*)'|"((?:[^"\\]|\\.)*)"|\\(.)/g, (whole, single, double, escaped) => single ?? escaped ?? double.replace(/\\([$`"\\])/g, "$1"));
  /* git's own options that take the next word as their value, when it is not given with "=". */
  const GIT_VALUES = ["-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env", "--super-prefix"];
  const ASSIGNMENT = /^[A-Za-z_][A-Za-z0-9_]*=/;

  /* A line's shell commands, each a list of words. */
  function shellCommands(line) {
    const commands = [[]];
    for (const [, operator, word] of line.matchAll(TOKENS)) {
      if (operator) commands.push([]);
      else if (word) commands[commands.length - 1].push(unquote(word));
    }
    return commands.filter((words) => words.length > 0);
  }

  /* A shell command's git subcommand, after any VAR=value words, git (by any path) and git's own
     options; null when it is not git or names no subcommand. */
  function gitSubcommand(words) {
    const start = words.findIndex((word) => !ASSIGNMENT.test(word));
    if (start < 0 || words[start].split("/").pop() !== "git") return null;
    let at = start + 1;
    while (at < words.length && words[at].startsWith("-")) at += GIT_VALUES.includes(words[at]) ? 2 : 1;
    return words[at] || null;
  }

  const gitCommands = (lines) => lines.filter((typed) => typed.status === 0).flatMap((typed) => shellCommands(typed.line).map(gitSubcommand).filter(Boolean));

  return { gitCommands };
})();
