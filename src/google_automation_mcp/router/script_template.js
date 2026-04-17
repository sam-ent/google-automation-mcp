// Google Automation MCP — Apps Script Router
// Deployed as a Web App. Called via HTTP POST from the MCP server.
// Each request must include a secret token for authentication.

var SECRET = '{{MCP_SECRET}}';

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
  'search_gmail': searchGmail,
  'get_gmail_message': getGmailMessage,
  'send_gmail': sendGmail,
  'list_gmail_labels': listGmailLabels,
  'modify_gmail_labels': modifyGmailLabels
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
  if (!msg) {
    throw new Error('Message not found: ' + p.message_id);
  }
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
    id: msg.getId(),
    thread_id: msg.getThread().getId(),
    subject: msg.getSubject(),
    from: msg.getFrom(),
    to: msg.getTo(),
    cc: msg.getCc(),
    bcc: msg.getBcc(),
    date: msg.getDate().toISOString(),
    body: msg.getPlainBody().substring(0, 5000),
    is_html: msg.getBody() !== msg.getPlainBody(),
    starred: msg.isStarred(),
    unread: msg.isUnread(),
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
  // System labels are not accessible via GmailApp, note that
  return {
    user_labels: userLabels,
    note: 'System labels (INBOX, SENT, etc.) are not available via Apps Script GmailApp'
  };
}

function modifyGmailLabels(p) {
  var msg = GmailApp.getMessageById(p.message_id);
  if (!msg) {
    throw new Error('Message not found: ' + p.message_id);
  }
  var thread = msg.getThread();
  var added = [];
  var removed = [];

  if (p.add_labels) {
    for (var i = 0; i < p.add_labels.length; i++) {
      var labelName = p.add_labels[i];
      // Handle system-like actions
      if (labelName === 'STARRED') { msg.star(); added.push('STARRED'); continue; }
      if (labelName === 'UNREAD') { msg.markUnread(); added.push('UNREAD'); continue; }
      if (labelName === 'TRASH') { msg.moveToTrash(); added.push('TRASH'); continue; }
      if (labelName === 'INBOX') { msg.getThread().moveToInbox(); added.push('INBOX'); continue; }
      // User label
      var label = GmailApp.getUserLabelByName(labelName);
      if (!label) label = GmailApp.createLabel(labelName);
      thread.addLabel(label);
      added.push(labelName);
    }
  }

  if (p.remove_labels) {
    for (var j = 0; j < p.remove_labels.length; j++) {
      var rlabelName = p.remove_labels[j];
      if (rlabelName === 'STARRED') { msg.unstar(); removed.push('STARRED'); continue; }
      if (rlabelName === 'UNREAD') { msg.markRead(); removed.push('UNREAD'); continue; }
      if (rlabelName === 'INBOX') { thread.moveToArchive(); removed.push('INBOX'); continue; }
      var rlabel = GmailApp.getUserLabelByName(rlabelName);
      if (rlabel) { thread.removeLabel(rlabel); removed.push(rlabelName); }
    }
  }

  return {message_id: p.message_id, added: added, removed: removed};
}
