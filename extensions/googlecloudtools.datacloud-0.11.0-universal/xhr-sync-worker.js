/**
 * @license
 * Copyright (c) 2010 Elijah Insua
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use,
 * copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following
 * conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 */

"use strict";
/* eslint-disable no-process-exit */
const util = require("util");
const { JSDOM } = require("../../../..");
const { READY_STATES } = require("./xhr-utils");
const idlUtils = require("../generated/utils");
const tough = require("tough-cookie");

const dom = new JSDOM();
const xhr = new dom.window.XMLHttpRequest();
const xhrImpl = idlUtils.implForWrapper(xhr);

const chunks = [];

process.stdin.on("data", chunk => {
  chunks.push(chunk);
});

process.stdin.on("end", () => {
  const buffer = Buffer.concat(chunks);

  const flag = JSON.parse(buffer.toString());
  if (flag.body && flag.body.type === "Buffer" && flag.body.data) {
    flag.body = Buffer.from(flag.body.data);
  }
  if (flag.cookieJar) {
    flag.cookieJar = tough.CookieJar.fromJSON(flag.cookieJar);
  }

  flag.synchronous = false;
  Object.assign(xhrImpl.flag, flag);
  const { properties } = xhrImpl;
  xhrImpl.readyState = READY_STATES.OPENED;
  try {
    xhr.addEventListener("loadend", () => {
      if (properties.error) {
        properties.error = properties.error.stack || util.inspect(properties.error);
      }
      process.stdout.write(JSON.stringify({
        responseURL: xhrImpl.responseURL,
        status: xhrImpl.status,
        statusText: xhrImpl.statusText,
        properties
      }), () => {
        process.exit(0);
      });
    }, false);
    xhr.send(flag.body);
  } catch (error) {
    properties.error += error.stack || util.inspect(error);
    process.stdout.write(JSON.stringify({
      responseURL: xhrImpl.responseURL,
      status: xhrImpl.status,
      statusText: xhrImpl.statusText,
      properties
    }), () => {
      process.exit(0);
    });
  }
});
