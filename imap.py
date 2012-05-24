import imaplib
import socket
from porkchop.plugin import PorkchopPlugin


class ImapPlugin(PorkchopPlugin):
    def get_data(self):
        data = self.gendict()
        config = self.config.get('imap', {})

        imap_user = config.get('user', 'username')
        imap_password = config.get('password', 'password')
        imap_host = config.get('host', 'localhost')
        imap_port = config.get('port', 143)
        imap_mailboxes = config.get('mailboxes', 'INBOX')

        mailboxes = imap_mailboxes.split(',')
    
        try:
            M = imaplib.IMAP4(imap_host, imap_port)
            M.login(imap_login, imap_password)
        except (socket.error, imaplib.IMAP4.error):
            return {}

        for mailbox in mailboxes:
            box = M.select(mailbox, True)
            # Couldn't select mailbox
            if box[0] == 'NO':
                continue

            resp = M.search(None, 'UnSeen')
            # ('OK', ['1 2 3 4'])
            if resp[0] == 'OK':
                unread = resp[1][0].split(' ')
            else:
                unread = []
            data[mailbox.lower()]['unread'] = len(unread)

        return data

