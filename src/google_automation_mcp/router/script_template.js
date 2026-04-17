// Google Automation MCP — Apps Script Router
// Deployed as a Web App. Called via HTTP POST from the MCP server.
// Each request must include a secret token for authentication.

var SECRET = '{{MCP_SECRET}}';

function doGet() {
  // Touch services that require explicit scope activation.
  // Without these calls, manifest-only scopes may not trigger consent.
  try { UrlFetchApp.fetch('https://www.googleapis.com/tasks/v1/users/@me/lists?maxResults=1', {
    headers: {'Authorization': 'Bearer ' + ScriptApp.getOAuthToken()}, muteHttpExceptions: true
  }); } catch(e) {}
  return HtmlService.createHtmlOutput(
    '<h2>MCP Router authorized</h2>' +
    '<p>All Google Workspace scopes granted. You can close this tab.</p>'
  );
}

function doPost(e) {
  var payload = JSON.parse(e.postData.contents);
  if (payload.secret !== SECRET) {
    return _json({error: 'unauthorized', code: 403});
  }
  var handler = ROUTES[payload.action];
  if (!handler) {
    return _json({error: 'unknown action: ' + payload.action, code: 400});
  }
  try {
    var result = handler(payload.params || {});
    return _json({result: result});
  } catch (err) {
    return _json({error: err.message, stack: err.stack, code: 500});
  }
}

function _json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

// =============================================================================
// Route Table
// =============================================================================

var ROUTES = {
  // Gmail
  'search_gmail': searchGmail,
  'get_gmail_message': getGmailMessage,
  'send_gmail': sendGmail,
  'list_gmail_labels': listGmailLabels,
  'modify_gmail_labels': modifyGmailLabels,
  // Drive
  'search_drive': searchDrive,
  'list_drive': listDrive,
  'get_drive_content': getDriveContent,
  'create_drive_file': createDriveFile,
  'create_drive_folder': createDriveFolder,
  'delete_drive_file': deleteDriveFile,
  'trash_drive_file': trashDriveFile,
  'share_drive_file': shareDriveFile,
  'list_drive_permissions': listDrivePermissions,
  'remove_drive_permission': removeDrivePermission,
  // Sheets
  'list_spreadsheets': listSpreadsheets,
  'get_sheet_values': getSheetValues,
  'update_sheet_values': updateSheetValues,
  'append_sheet_values': appendSheetValues,
  'create_spreadsheet': createSpreadsheet,
  'get_spreadsheet_metadata': getSpreadsheetMetadata,
  // Calendar
  'list_calendars': listCalendars,
  'get_events': getEvents,
  'create_event': createEvent,
  'update_event': updateEvent,
  'delete_event': deleteEvent,
  // Docs
  'search_docs': searchDocs,
  'get_doc_content': getDocContent,
  'create_doc': createDoc,
  'modify_doc_text': modifyDocText,
  'append_doc_text': appendDocText,
  // Forms
  'get_form': getForm,
  'create_form': createForm,
  'add_form_question': addFormQuestion,
  'get_form_responses': getFormResponses,
  // Tasks
  'list_task_lists': listTaskLists,
  'get_tasks': getTasks,
  'create_task': createTask,
  'update_task': updateTask,
  'delete_task': deleteTask,
  'complete_task': completeTask
};

// =============================================================================
// Gmail Handlers
// =============================================================================

function searchGmail(p) {
  var query = p.query || '';
  var maxResults = p.max_results || 10;
  var threads = GmailApp.search(query, 0, maxResults);
  var results = [];
  for (var i = 0; i < threads.length; i++) {
    var thread = threads[i];
    var msgs = thread.getMessages();
    var first = msgs[0];
    var labels = thread.getLabels();
    var labelNames = [];
    for (var j = 0; j < labels.length; j++) {
      labelNames.push(labels[j].getName());
    }
    results.push({
      id: thread.getId(),
      message_id: first.getId(),
      subject: first.getSubject(),
      from: first.getFrom(),
      to: first.getTo(),
      date: first.getDate().toISOString(),
      snippet: first.getPlainBody().substring(0, 200),
      labels: labelNames,
      unread: thread.isUnread(),
      message_count: msgs.length
    });
  }
  return results;
}

function getGmailMessage(p) {
  var msg = GmailApp.getMessageById(p.message_id);
  if (!msg) throw new Error('Message not found: ' + p.message_id);
  var attachments = msg.getAttachments();
  var attachmentInfo = [];
  for (var i = 0; i < attachments.length; i++) {
    attachmentInfo.push({
      name: attachments[i].getName(),
      type: attachments[i].getContentType(),
      size: attachments[i].getSize()
    });
  }
  return {
    id: msg.getId(), thread_id: msg.getThread().getId(),
    subject: msg.getSubject(), from: msg.getFrom(), to: msg.getTo(),
    cc: msg.getCc(), bcc: msg.getBcc(),
    date: msg.getDate().toISOString(),
    body: msg.getPlainBody().substring(0, 5000),
    is_html: msg.getBody() !== msg.getPlainBody(),
    starred: msg.isStarred(), unread: msg.isUnread(),
    attachments: attachmentInfo
  };
}

function sendGmail(p) {
  var options = {};
  if (p.cc) options.cc = p.cc;
  if (p.bcc) options.bcc = p.bcc;
  if (p.html) {
    options.htmlBody = p.body;
    GmailApp.sendEmail(p.to, p.subject, '', options);
  } else {
    GmailApp.sendEmail(p.to, p.subject, p.body, options);
  }
  return {sent: true, to: p.to, subject: p.subject};
}

function listGmailLabels(p) {
  var labels = GmailApp.getUserLabels();
  var userLabels = [];
  for (var i = 0; i < labels.length; i++) {
    userLabels.push({name: labels[i].getName()});
  }
  return {
    user_labels: userLabels,
    note: 'System labels (INBOX, SENT, etc.) are not available via Apps Script GmailApp'
  };
}

function modifyGmailLabels(p) {
  var msg = GmailApp.getMessageById(p.message_id);
  if (!msg) throw new Error('Message not found: ' + p.message_id);
  var thread = msg.getThread();
  var added = [], removed = [];
  if (p.add_labels) {
    for (var i = 0; i < p.add_labels.length; i++) {
      var ln = p.add_labels[i];
      if (ln === 'STARRED') { msg.star(); added.push(ln); continue; }
      if (ln === 'UNREAD') { msg.markUnread(); added.push(ln); continue; }
      if (ln === 'TRASH') { msg.moveToTrash(); added.push(ln); continue; }
      if (ln === 'INBOX') { thread.moveToInbox(); added.push(ln); continue; }
      var label = GmailApp.getUserLabelByName(ln);
      if (!label) label = GmailApp.createLabel(ln);
      thread.addLabel(label);
      added.push(ln);
    }
  }
  if (p.remove_labels) {
    for (var j = 0; j < p.remove_labels.length; j++) {
      var rn = p.remove_labels[j];
      if (rn === 'STARRED') { msg.unstar(); removed.push(rn); continue; }
      if (rn === 'UNREAD') { msg.markRead(); removed.push(rn); continue; }
      if (rn === 'INBOX') { thread.moveToArchive(); removed.push(rn); continue; }
      var rl = GmailApp.getUserLabelByName(rn);
      if (rl) { thread.removeLabel(rl); removed.push(rn); }
    }
  }
  return {message_id: p.message_id, added: added, removed: removed};
}

// =============================================================================
// Drive Handlers
// =============================================================================

function searchDrive(p) {
  var query = p.query || '';
  var maxResults = p.page_size || 10;
  var files, iter;
  if (query.indexOf('contains') >= 0 || query.indexOf('=') >= 0) {
    iter = DriveApp.searchFiles(query);
  } else {
    iter = DriveApp.searchFiles("fullText contains '" + query.replace(/'/g, "\\'") + "'");
  }
  var results = [];
  while (iter.hasNext() && results.length < maxResults) {
    var f = iter.next();
    results.push({
      id: f.getId(), name: f.getName(), mime_type: f.getMimeType(),
      size: f.getSize(), modified: f.getLastUpdated().toISOString(),
      url: f.getUrl()
    });
  }
  return results;
}

function listDrive(p) {
  var folderId = p.folder_id || 'root';
  var maxResults = p.page_size || 50;
  var folder = (folderId === 'root') ? DriveApp.getRootFolder() : DriveApp.getFolderById(folderId);
  var results = {folders: [], files: []};
  var folders = folder.getFolders();
  while (folders.hasNext() && results.folders.length < maxResults) {
    var fo = folders.next();
    results.folders.push({id: fo.getId(), name: fo.getName()});
  }
  var files = folder.getFiles();
  while (files.hasNext() && results.files.length < maxResults) {
    var fi = files.next();
    results.files.push({
      id: fi.getId(), name: fi.getName(), mime_type: fi.getMimeType(),
      size: fi.getSize()
    });
  }
  return results;
}

function getDriveContent(p) {
  var file = DriveApp.getFileById(p.file_id);
  var mime = file.getMimeType();
  var content;
  if (mime === 'application/vnd.google-apps.document') {
    var doc = DocumentApp.openById(p.file_id);
    content = doc.getBody().getText();
  } else if (mime === 'application/vnd.google-apps.spreadsheet') {
    var ss = SpreadsheetApp.openById(p.file_id);
    var sheet = ss.getActiveSheet();
    var data = sheet.getDataRange().getValues();
    content = data.map(function(row) { return row.join(','); }).join('\n');
  } else {
    content = file.getBlob().getDataAsString();
  }
  return {
    id: file.getId(), name: file.getName(), mime_type: mime,
    url: file.getUrl(), content: content.substring(0, 50000)
  };
}

function createDriveFile(p) {
  var folder = (p.folder_id && p.folder_id !== 'root')
    ? DriveApp.getFolderById(p.folder_id) : DriveApp.getRootFolder();
  var blob = Utilities.newBlob(p.content || '', p.mime_type || 'text/plain', p.file_name);
  var file = folder.createFile(blob);
  return {id: file.getId(), name: file.getName(), url: file.getUrl()};
}

function createDriveFolder(p) {
  var parent = (p.parent_id && p.parent_id !== 'root')
    ? DriveApp.getFolderById(p.parent_id) : DriveApp.getRootFolder();
  var folder = parent.createFolder(p.folder_name);
  return {id: folder.getId(), name: folder.getName(), url: folder.getUrl()};
}

function deleteDriveFile(p) {
  DriveApp.getFileById(p.file_id).setTrashed(true);
  Drive.Files.remove(p.file_id);
  return {deleted: true, file_id: p.file_id};
}

function trashDriveFile(p) {
  DriveApp.getFileById(p.file_id).setTrashed(true);
  return {trashed: true, file_id: p.file_id};
}

function shareDriveFile(p) {
  var file = DriveApp.getFileById(p.file_id);
  var role = p.role || 'reader';
  if (role === 'writer' || role === 'owner') {
    file.addEditor(p.email);
  } else if (role === 'commenter') {
    file.addCommenter(p.email);
  } else {
    file.addViewer(p.email);
  }
  return {shared: true, file_id: p.file_id, email: p.email, role: role};
}

function listDrivePermissions(p) {
  var file = DriveApp.getFileById(p.file_id);
  var editors = file.getEditors().map(function(u) {
    return {email: u.getEmail(), role: 'writer'};
  });
  var viewers = file.getViewers().map(function(u) {
    return {email: u.getEmail(), role: 'reader'};
  });
  return {file_id: p.file_id, permissions: editors.concat(viewers)};
}

function removeDrivePermission(p) {
  var file = DriveApp.getFileById(p.file_id);
  file.removeEditor(p.permission_id);
  file.removeViewer(p.permission_id);
  return {removed: true, file_id: p.file_id, permission_id: p.permission_id};
}

// =============================================================================
// Sheets Handlers
// =============================================================================

function listSpreadsheets(p) {
  var query = "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false";
  if (p.query) query += " and name contains '" + p.query.replace(/'/g, "\\'") + "'";
  var iter = DriveApp.searchFiles(query);
  var results = [];
  var max = p.page_size || 20;
  while (iter.hasNext() && results.length < max) {
    var f = iter.next();
    results.push({
      id: f.getId(), name: f.getName(),
      modified: f.getLastUpdated().toISOString(), url: f.getUrl()
    });
  }
  return results;
}

function getSheetValues(p) {
  var ss = SpreadsheetApp.openById(p.spreadsheet_id);
  var range = p.range || 'Sheet1';
  var sheet, dataRange;
  if (range.indexOf('!') >= 0) {
    var parts = range.split('!');
    sheet = ss.getSheetByName(parts[0]);
    dataRange = sheet.getRange(parts[1]);
  } else {
    sheet = ss.getSheetByName(range) || ss.getSheets()[0];
    dataRange = sheet.getDataRange();
  }
  return {
    spreadsheet_id: p.spreadsheet_id, range: range,
    values: dataRange.getValues()
  };
}

function updateSheetValues(p) {
  var ss = SpreadsheetApp.openById(p.spreadsheet_id);
  var parts = p.range.split('!');
  var sheet = (parts.length > 1) ? ss.getSheetByName(parts[0]) : ss.getSheets()[0];
  var rangeStr = (parts.length > 1) ? parts[1] : parts[0];
  var range = sheet.getRange(rangeStr);
  range.setValues(p.values);
  return {
    spreadsheet_id: p.spreadsheet_id, range: p.range,
    updated_rows: p.values.length, updated_cells: p.values.length * p.values[0].length
  };
}

function appendSheetValues(p) {
  var ss = SpreadsheetApp.openById(p.spreadsheet_id);
  var sheetName = p.range ? p.range.split('!')[0] : null;
  var sheet = sheetName ? (ss.getSheetByName(sheetName) || ss.getSheets()[0]) : ss.getSheets()[0];
  var lastRow = sheet.getLastRow();
  var startRow = lastRow + 1;
  var range = sheet.getRange(startRow, 1, p.values.length, p.values[0].length);
  range.setValues(p.values);
  return {
    spreadsheet_id: p.spreadsheet_id,
    updated_range: sheet.getName() + '!A' + startRow,
    updated_rows: p.values.length, updated_cells: p.values.length * p.values[0].length
  };
}

function createSpreadsheet(p) {
  var ss = SpreadsheetApp.create(p.title);
  var sheets = [];
  if (p.sheet_names && p.sheet_names.length > 0) {
    var first = ss.getSheets()[0];
    first.setName(p.sheet_names[0]);
    sheets.push(p.sheet_names[0]);
    for (var i = 1; i < p.sheet_names.length; i++) {
      ss.insertSheet(p.sheet_names[i]);
      sheets.push(p.sheet_names[i]);
    }
  } else {
    sheets.push(ss.getSheets()[0].getName());
  }
  return {
    spreadsheet_id: ss.getId(), title: p.title,
    sheets: sheets, url: ss.getUrl()
  };
}

function getSpreadsheetMetadata(p) {
  var ss = SpreadsheetApp.openById(p.spreadsheet_id);
  var sheets = ss.getSheets().map(function(s) {
    return {
      title: s.getName(), sheet_id: s.getSheetId(),
      rows: s.getMaxRows(), cols: s.getMaxColumns()
    };
  });
  return {
    spreadsheet_id: p.spreadsheet_id, title: ss.getName(),
    sheets: sheets, url: ss.getUrl()
  };
}

// =============================================================================
// Calendar Handlers
// =============================================================================

function listCalendars(p) {
  var cals = CalendarApp.getAllCalendars();
  return cals.map(function(c) {
    return {
      id: c.getId(), name: c.getName(),
      is_primary: c.isMyPrimaryCalendar()
    };
  });
}

function getEvents(p) {
  var calId = p.calendar_id || 'primary';
  var cal = (calId === 'primary') ? CalendarApp.getDefaultCalendar() : CalendarApp.getCalendarById(calId);
  if (!cal) throw new Error('Calendar not found: ' + calId);
  var now = new Date();
  var start = p.time_min ? new Date(p.time_min) : now;
  var end = p.time_max ? new Date(p.time_max) : new Date(now.getTime() + 7*24*60*60*1000);
  var events = cal.getEvents(start, end);
  if (p.query) {
    var q = p.query.toLowerCase();
    events = events.filter(function(e) {
      return e.getTitle().toLowerCase().indexOf(q) >= 0;
    });
  }
  var max = p.max_results || 10;
  return events.slice(0, max).map(function(e) {
    return {
      id: e.getId(), summary: e.getTitle(),
      start: e.getStartTime().toISOString(), end: e.getEndTime().toISOString(),
      location: e.getLocation(), description: e.getDescription(),
      all_day: e.isAllDayEvent()
    };
  });
}

function createEvent(p) {
  var calId = p.calendar_id || 'primary';
  var cal = (calId === 'primary') ? CalendarApp.getDefaultCalendar() : CalendarApp.getCalendarById(calId);
  if (!cal) throw new Error('Calendar not found: ' + calId);
  var ev;
  var options = {};
  if (p.description) options.description = p.description;
  if (p.location) options.location = p.location;
  if (p.all_day) {
    ev = cal.createAllDayEvent(p.summary, new Date(p.start_time), new Date(p.end_time), options);
  } else {
    ev = cal.createEvent(p.summary, new Date(p.start_time), new Date(p.end_time), options);
  }
  if (p.attendees) {
    var emails = p.attendees.split(',');
    for (var i = 0; i < emails.length; i++) ev.addGuest(emails[i].trim());
  }
  return {
    id: ev.getId(), summary: ev.getTitle(),
    start: ev.getStartTime().toISOString(), calendar_id: calId
  };
}

function updateEvent(p) {
  var calId = p.calendar_id || 'primary';
  var cal = (calId === 'primary') ? CalendarApp.getDefaultCalendar() : CalendarApp.getCalendarById(calId);
  if (!cal) throw new Error('Calendar not found: ' + calId);
  var ev = cal.getEventById(p.event_id);
  if (!ev) throw new Error('Event not found: ' + p.event_id);
  if (p.summary !== undefined) ev.setTitle(p.summary);
  if (p.description !== undefined) ev.setDescription(p.description);
  if (p.location !== undefined) ev.setLocation(p.location);
  if (p.start_time && p.end_time) ev.setTime(new Date(p.start_time), new Date(p.end_time));
  return {
    id: ev.getId(), summary: ev.getTitle(),
    start: ev.getStartTime().toISOString(), calendar_id: calId
  };
}

function deleteEvent(p) {
  var calId = p.calendar_id || 'primary';
  var cal = (calId === 'primary') ? CalendarApp.getDefaultCalendar() : CalendarApp.getCalendarById(calId);
  if (!cal) throw new Error('Calendar not found: ' + calId);
  var ev = cal.getEventById(p.event_id);
  if (!ev) throw new Error('Event not found: ' + p.event_id);
  ev.deleteEvent();
  return {deleted: true, event_id: p.event_id, calendar_id: calId};
}

// =============================================================================
// Docs Handlers
// =============================================================================

function searchDocs(p) {
  var q = (p.query || '').replace(/'/g, "\\'");
  var query = "mimeType = 'application/vnd.google-apps.document' and trashed = false and title contains '" + q + "'";
  var iter = DriveApp.searchFiles(query);
  var results = [];
  var max = p.page_size || 10;
  while (iter.hasNext() && results.length < max) {
    var f = iter.next();
    results.push({
      id: f.getId(), name: f.getName(),
      modified: f.getLastUpdated().toISOString(), url: f.getUrl()
    });
  }
  return results;
}

function getDocContent(p) {
  var doc = DocumentApp.openById(p.document_id);
  return {
    document_id: p.document_id, title: doc.getName(),
    content: doc.getBody().getText(),
    url: doc.getUrl()
  };
}

function createDoc(p) {
  var doc = DocumentApp.create(p.title);
  if (p.content) doc.getBody().setText(p.content);
  return {document_id: doc.getId(), title: doc.getName(), url: doc.getUrl()};
}

function modifyDocText(p) {
  var doc = DocumentApp.openById(p.document_id);
  var body = doc.getBody();
  if (p.replace_text) {
    body.replaceText(p.replace_text, p.text);
    return {document_id: p.document_id, action: 'replace', url: doc.getUrl()};
  } else {
    var index = p.index || 0;
    if (index <= 0) {
      body.insertParagraph(0, p.text);
    } else {
      body.insertParagraph(index, p.text);
    }
    return {document_id: p.document_id, action: 'insert', index: index, url: doc.getUrl()};
  }
}

function appendDocText(p) {
  var doc = DocumentApp.openById(p.document_id);
  doc.getBody().appendParagraph(p.text);
  return {document_id: p.document_id, url: doc.getUrl()};
}

// =============================================================================
// Forms Handlers
// =============================================================================

function getForm(p) {
  var form = FormApp.openById(p.form_id);
  var items = form.getItems().map(function(item, idx) {
    return {
      index: idx + 1, title: item.getTitle(),
      item_id: item.getId(), type: item.getType().toString()
    };
  });
  return {
    form_id: form.getId(), title: form.getTitle(),
    description: form.getDescription(),
    url: form.getPublishedUrl(), edit_url: form.getEditUrl(),
    items: items
  };
}

function createForm(p) {
  var form = FormApp.create(p.title);
  if (p.description) form.setDescription(p.description);
  return {
    form_id: form.getId(), title: form.getTitle(),
    url: form.getPublishedUrl(), edit_url: form.getEditUrl()
  };
}

function addFormQuestion(p) {
  var form = FormApp.openById(p.form_id);
  var item;
  var type = (p.question_type || 'TEXT').toUpperCase();
  if (type === 'MULTIPLE_CHOICE') {
    item = form.addMultipleChoiceItem().setTitle(p.title);
    if (p.choices) item.setChoiceValues(p.choices.split(',').map(function(c) { return c.trim(); }));
  } else if (type === 'CHECKBOX') {
    item = form.addCheckboxItem().setTitle(p.title);
    if (p.choices) item.setChoiceValues(p.choices.split(',').map(function(c) { return c.trim(); }));
  } else if (type === 'DROP_DOWN') {
    item = form.addListItem().setTitle(p.title);
    if (p.choices) item.setChoiceValues(p.choices.split(',').map(function(c) { return c.trim(); }));
  } else if (type === 'PARAGRAPH') {
    item = form.addParagraphTextItem().setTitle(p.title);
  } else if (type === 'SCALE') {
    item = form.addScaleItem().setTitle(p.title).setBounds(1, 5);
  } else {
    item = form.addTextItem().setTitle(p.title);
  }
  if (p.required && item.setRequired) item.setRequired(true);
  return {form_id: p.form_id, title: p.title, type: type};
}

function getFormResponses(p) {
  var form = FormApp.openById(p.form_id);
  var responses = form.getResponses();
  var max = p.max_results || 50;
  var results = [];
  var start = Math.max(0, responses.length - max);
  for (var i = start; i < responses.length; i++) {
    var r = responses[i];
    var answers = r.getItemResponses().map(function(ir) {
      return {question: ir.getItem().getTitle(), answer: ir.getResponse()};
    });
    results.push({
      response_id: r.getId(), timestamp: r.getTimestamp().toISOString(),
      answers: answers
    });
  }
  return results;
}

// =============================================================================
// Tasks Handlers (via REST API + UrlFetchApp, no advanced service needed)
// =============================================================================

function _tasksApi(method, path, body) {
  var url = 'https://tasks.googleapis.com/tasks/v1' + path;
  var opts = {
    method: method,
    headers: {'Authorization': 'Bearer ' + ScriptApp.getOAuthToken()},
    contentType: 'application/json',
    muteHttpExceptions: true
  };
  if (body) opts.payload = JSON.stringify(body);
  var resp = UrlFetchApp.fetch(url, opts);
  var code = resp.getResponseCode();
  if (code >= 400) throw new Error('Tasks API ' + code + ': ' + resp.getContentText());
  var text = resp.getContentText();
  return text ? JSON.parse(text) : {};
}

function listTaskLists(p) {
  var max = p.max_results || 20;
  var data = _tasksApi('get', '/users/@me/lists?maxResults=' + max);
  return (data.items || []).map(function(tl) {
    return {id: tl.id, title: tl.title, updated: tl.updated};
  });
}

function getTasks(p) {
  var listId = p.tasklist_id || '@default';
  var qs = '?maxResults=' + (p.max_results || 20);
  if (p.show_completed === false) qs += '&showCompleted=false';
  if (p.show_hidden) qs += '&showHidden=true';
  var data = _tasksApi('get', '/lists/' + encodeURIComponent(listId) + '/tasks' + qs);
  return (data.items || []).map(function(t) {
    return {id: t.id, title: t.title, status: t.status, due: t.due || null, notes: t.notes || null};
  });
}

function createTask(p) {
  var listId = p.tasklist_id || '@default';
  var body = {title: p.title};
  if (p.notes) body.notes = p.notes;
  if (p.due) body.due = p.due;
  var task = _tasksApi('post', '/lists/' + encodeURIComponent(listId) + '/tasks', body);
  return {id: task.id, title: task.title, status: task.status, due: task.due || null};
}

function updateTask(p) {
  var listId = p.tasklist_id || '@default';
  var existing = _tasksApi('get', '/lists/' + encodeURIComponent(listId) + '/tasks/' + encodeURIComponent(p.task_id));
  if (p.title !== undefined) existing.title = p.title;
  if (p.notes !== undefined) existing.notes = p.notes;
  if (p.due !== undefined) existing.due = p.due;
  if (p.status !== undefined) existing.status = p.status;
  var updated = _tasksApi('put', '/lists/' + encodeURIComponent(listId) + '/tasks/' + encodeURIComponent(p.task_id), existing);
  return {id: updated.id, title: updated.title, status: updated.status, due: updated.due || null};
}

function deleteTask(p) {
  var listId = p.tasklist_id || '@default';
  _tasksApi('delete', '/lists/' + encodeURIComponent(listId) + '/tasks/' + encodeURIComponent(p.task_id));
  return {deleted: true, task_id: p.task_id, tasklist_id: listId};
}

function completeTask(p) {
  var listId = p.tasklist_id || '@default';
  var existing = _tasksApi('get', '/lists/' + encodeURIComponent(listId) + '/tasks/' + encodeURIComponent(p.task_id));
  existing.status = 'completed';
  var updated = _tasksApi('put', '/lists/' + encodeURIComponent(listId) + '/tasks/' + encodeURIComponent(p.task_id), existing);
  return {id: updated.id, title: updated.title, status: 'completed'};
}
