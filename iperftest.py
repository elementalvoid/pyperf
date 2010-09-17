#!/usr/bin/env python

import sys
from optparse import OptionParser
from subprocess import Popen, PIPE
from dataformatter import DataFormatter

class IPerfTest(object):
    """
    A single iperf test.  Keeps track of up and down statistics for later use.
    Each test instance must have an identifier, if not defined a value will be
    assigned (defaults to -1).
    """
    IPERF_PORT = 5001
    PRINT_WIDTH = 80

    #Data tuple locations
    TIMESTAMP = 0
    CLIENT_IP = 1
    CLIENT_PORT = 2
    SERVER_IP = 3
    SERVER_PORT = 4
    TEST_ID = 5
    TIME_RANGE = 6
    TRANSFERED = 7
    SPEED = 8

    def __init__(self, server, id=-1, description='', time=15, window='64k',
                 interval=1, csvfile=None, summaryfile=None, cli=False):
        self.server = server
        self.id = id
        self.description = description
        self.time = time
        self.window = window
        self.interval = interval
        self.csvfile = csvfile
        self.summaryfile = summaryfile
        self.cli = cli
        self.subprocess = None
        self.iperf_cmd = 'iperf -c %s -t %d -w %s -r -i %s -y C' % \
                         (server, time, window, interval)
        self.iperf_up_data = []
        self.up_speed_min = -1
        self.up_speed_max = -1
        self.iperf_down_data = []
        self.down_speed_min = -1
        self.down_speed_max = -1

    def process_up_csv(self, data):
        current_speed = int(data[IPerfTest.SPEED])
        if current_speed < self.up_speed_min or self.up_speed_min == -1:
            self.up_speed_min = current_speed
        if current_speed > self.up_speed_max or self.up_speed_max == -1:
            self.up_speed_max = current_speed
        self.iperf_up_data.append(data)

    def process_down_csv(self, data):
        current_speed = int(data[IPerfTest.SPEED])
        if current_speed < self.down_speed_min or self.down_speed_min == -1:
            self.down_speed_min = current_speed
        if current_speed > self.down_speed_max or self.down_speed_max == -1:
            self.down_speed_max = current_speed
        self.iperf_down_data.append(data)

    def process_csv(self, csv_line, updown):
        data = csv_line.split(',')
        if self.cli:
            print ' %s sec \t%s\t%s/sec' % \
                  (data[self.TIME_RANGE],
                   DataFormatter.format_bytes(data[IPerfTest.TRANSFERED]),
                   DataFormatter.format_bits(data[IPerfTest.SPEED])
                  )
        if updown == 'up':
            self.process_up_csv(data)
        else:
            self.process_down_csv(data)

    def get_up_transferred(self):
        return float(self.iperf_up_data[-1][IPerfTest.TRANSFERED])

    def get_up_speed(self):
        return float(self.iperf_up_data[-1][IPerfTest.SPEED])

    def get_up_speed_min(self):
        return float(self.up_speed_min)

    def get_up_speed_max(self):
        return float(self.up_speed_max)

    def get_down_transferred(self):
        return float(self.iperf_down_data[-1][IPerfTest.TRANSFERED])

    def get_down_speed(self):
        return float(self.iperf_down_data[-1][IPerfTest.SPEED])

    def get_down_speed_min(self):
        return float(self.down_speed_min)

    def get_down_speed_max(self):
        return float(self.down_speed_max)

    def get_up_jitter(self):
        diff = float(self.up_speed_max - self.up_speed_min)
        return (diff / self.get_up_speed() * 100)

    def get_down_jitter(self):
        diff = float(self.down_speed_max - self.down_speed_min)
        return (diff / self.get_down_speed() * 100)

    def test_server_alive(self):
        #TODO: Don't exit. Throw an exception instead.
        try:
            import socket
            sock = socket.socket()
            sock.settimeout(2)
            sock.connect((self.server, IPerfTest.IPERF_PORT))
            sock.close()
        except socket.error as sockerror:
            error = 'Could not connect to iperf server at %s:%s ' % \
                   (self.server, IPerfTest.IPERF_PORT) + '(' + str(sockerror[1]) + ')'
            raise Exception(error)

    def get_header(self):
        header = '-' * IPerfTest.PRINT_WIDTH + '\n'
        header += '|%s|\n' % self.description.center(IPerfTest.PRINT_WIDTH - 2)
        header += '|%s|\n' % ''.join(('Test #', str(self.id))).center(IPerfTest.PRINT_WIDTH - 2)
        header += '-' * IPerfTest.PRINT_WIDTH + '\n'
        return header

    def print_header(self):
        print self.get_header(),

    def get_summary(self):
        try:
            summary = 'Upload:\n'
            summary += '  %s: %s\t%s: %s\n' % \
                  ('Transferred'.ljust(11), DataFormatter.format_bytes(self.get_up_transferred()),
                   'Speed'.ljust(11), DataFormatter.format_bits(self.get_up_speed()))
            summary += '  %s: %s\t%s: %s\n' % \
                  ('Min'.ljust(11), DataFormatter.format_bits(self.get_up_speed_min()),
                   'Max'.ljust(11), DataFormatter.format_bits(self.get_up_speed_max()))
            summary += '  %s: %2.2f%%\n' % ('Jitter'.ljust(11), self.get_up_jitter())
            summary += 'Download:\n'
            summary += '  %s: %s\t%s: %s\n' % \
                  ('Transferred'.ljust(11), DataFormatter.format_bytes(self.get_down_transferred()),
                   'Speed'.ljust(11), DataFormatter.format_bits(self.get_down_speed()))
            summary += '  %s: %s\t%s: %s\n' % \
                  ('Min'.ljust(11), DataFormatter.format_bits(self.get_down_speed_min()),
                   'Max'.ljust(11), DataFormatter.format_bits(self.get_down_speed_max()))
            summary += '  %s: %2.2f%%\n' % ('Jitter'.ljust(11), self.get_down_jitter())
            return summary
        except:
            pass

    def print_summary(self):
        print self.get_summary(),

    def run(self):
        self.test_server_alive()
        if self.csvfile:
            self.csvfile.writelines(self.get_header())
        self.subprocess = Popen(self.iperf_cmd, stdout=PIPE, stderr=PIPE, shell=True)
        line_count = 0
        if self.cli:
            print 'Upload In Progress:'
        while True:
            line = self.subprocess.stdout.readline().replace('\n', '')
            if line == '' and not self.subprocess.poll() == None:
                break
            updown = 'up' if (line_count < (self.time + 1)) else 'down'
            if self.cli and line_count == (self.time + 1):
                print 'Download In Progress:'
            line_count += 1
            if not len(line) == 0:
                if self.csvfile:
                    print >>self.csvfile, line
                self.process_csv(line, updown)
        if self.summaryfile:
            self.summaryfile.write(self.get_header())
            self.summaryfile.write(self.get_summary())

    def kill_subprocess(self):
        if self.subprocess == None:
            return
        try:
            self.subprocess.terminate()
        except:
            try:
                self.subprocess.kill()
            except:
                raise Exception('Popen terminate and kill failed.')

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('-c', '--client', dest='server',
                      help='iperf server to connect to', metavar='server_ip')
    parser.add_option('-t', '--time', dest='time', type='int', default=15,
                      help='time (in seconds) to run', metavar='test_time')
    parser.add_option('-i', '--interval', dest='interval', type='int', default=1,
                      help='interval to print data', metavar='update_interval')
    parser.add_option('-w', '--window', dest='window', type='string', default='64k',
                      help='iperf window size', metavar='tcp_window')
    parser.add_option('-d', '--description', dest='description', type='string',
                      help='test comment (location, antenna name, distance, etc.)',
                      metavar='description')
    parser.add_option('', '--csv-file', dest='csvfile', type='string',
                      default=None, help='csv filename', metavar='csvfile.csv')
    parser.add_option('', '--summary-file', dest='summaryfile', type='string',
                      default=None, help='summary filename', metavar='summaryfile.txt')
    (options, args) = parser.parse_args()
    required_options = ('--client', '--description')
    error_message = None
    for opt in required_options:
        opt_object = parser.get_option(opt)
        if eval('options.' + opt_object.dest) == None:
            if error_message == None:
                error_message = 'Error: %s is a required option.\n' % \
                                "/".join(opt_object._short_opts)
            else:
                error_message = '%s Error: %s is a required option.\n' % \
                                (error_message, "/".join(opt_object._short_opts))
        if not error_message == None:
            error_message = '\n %s \n %s' % (error_message, parser.format_help())
            parser.exit(status=2, msg=error_message)

    test = None
    try:
        csvfile = summaryfile = None
        csvfile_option = parser.get_option('--csv-file')
        summaryfile_option = parser.get_option('--summary-file')
        if not eval('options.' + csvfile_option.dest) == None:
            csvfile = open(options.csvfile, 'a+', 0)
        if not eval('options.' + summaryfile_option.dest) == None:
            summaryfile = open(options.summaryfile, 'a+', 0)

        test = IPerfTest(options.server, description=options.description,
                         time=options.time, window=options.window,
                         interval=options.interval, csvfile=csvfile,
                         summaryfile=summaryfile, cli=True)
        test.print_header()
        test.run()
        test.print_summary()
    except KeyboardInterrupt:
        print
        try:
            test.kill_subprocess()
        except:
            print 'Could not kill the iperf subprocess, you should do so manually.'
        sys.exit(0)
