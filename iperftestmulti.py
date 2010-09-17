#!/usr/bin/env python

import sys
from optparse import OptionParser
from iperftest import IPerfTest
from dataformatter import DataFormatter

class IPerfTestMulti(object):
    """
    Runs multipe IPerfTests and averages out the results.
    """

    def __init__(self, server, description='', num_tests=3, time=15,
                 window='64k', interval=1, csvfile=None, summaryfile=None,
                 cli=False):
        self.server = server
        self.description = description
        self.num_tests = num_tests
        self.time = time
        self.window = window
        self.interval = interval
        self.csvfile = csvfile
        self.summaryfile = summaryfile
        self.cli = cli
        self.tests = []
        self.total_up_min = -1
        self.total_up_max = -1
        self.total_down_min = -1
        self.total_down_max = -1
        self.total_up_transferred = 0.0
        self.total_up_speed = 0.0
        self.total_down_transferred = 0.0
        self.total_down_speed = 0.0

    def get_up_transferred(self):
        return self.total_up_transferred

    def get_down_transferred(self):
        return self.total_down_transferred

    def get_avg_up_speed(self):
        return self.total_up_speed / self.num_tests

    def get_avg_down_speed(self):
        return self.total_down_speed / self.num_tests

    def get_up_jitter(self):
        return (self.total_up_max - self.total_up_min) / self.total_up_speed * 100

    def get_down_jitter(self):
        return (self.total_down_max - self.total_down_min) / self.total_down_speed * 100

    def print_summary(self):
        print '-' * IPerfTest.PRINT_WIDTH
        print '|%s|' % self.description.center(IPerfTest.PRINT_WIDTH - 2)
        print '|%s|' % 'Summary'.center(IPerfTest.PRINT_WIDTH - 2)
        print '-' * IPerfTest.PRINT_WIDTH
        try:
            print 'Upload:'
            print '  %s: %s\t%s: %s' % \
                  ('Transferred'.ljust(11), DataFormatter.format_bytes(self.get_up_transferred()),
                   'Speed'.ljust(11), DataFormatter.format_bits(self.get_avg_up_speed()))
            print '  %s: %s\t%s: %s' % \
                  ('Min'.ljust(11), DataFormatter.format_bits(self.total_up_min),
                   'Max'.ljust(11), DataFormatter.format_bits(self.total_up_max))
            print '  %s: %2.2f%%' % ('Jitter'.ljust(11), self.get_up_jitter())
            print 'Download:'
            print '  %s: %s\t%s: %s' % \
                  ('Transferred'.ljust(11), DataFormatter.format_bytes(self.get_down_transferred()),
                   'Speed'.ljust(11), DataFormatter.format_bits(self.get_avg_down_speed()))
            print '  %s: %s\t%s: %s' % \
                  ('Min'.ljust(11), DataFormatter.format_bits(self.total_down_min),
                   'Max'.ljust(11), DataFormatter.format_bits(self.total_down_max))
            print '  %s: %2.2f%%' % ('Jitter'.ljust(11), self.get_down_jitter())
        except:
            pass

    def print_csv(self):
        print ','.join(('transferred', 'speed', 'min', 'max', 'jitter'))
        print ','.join((self.get_up_transferred(), self.get_avg_up_speed(),
                        self.total_up_min, self.total_up_max, self.get_up_jitter()))
        print ','.join((self.get_down_transferred(), self.get_avg_down_speed(),
                        self.total_down_min, self.total_down_max,
                        self.get_down_jitter()))

    def run(self):
        for test_num in range(1, self.num_tests + 1):
            test = IPerfTest(self.server, test_num, self.description,
                             self.time, self.window, self.interval,
                             self.csvfile, self.summaryfile, self.cli)
            self.tests.append(test)
            if self.cli:
                test.print_header()
            test.run()
            #if self.cli:
            test.print_summary()
            #sum all the up down cumulative values
            self.total_up_transferred += test.get_up_transferred()
            self.total_down_transferred += test.get_down_transferred()
            self.total_up_speed += test.get_up_speed()
            self.total_down_speed += test.get_down_speed()
            #update the min / max values
            if test.get_up_speed_min() < self.total_up_min or self.total_up_min == -1:
                self.total_up_min = test.get_up_speed_min()
            if test.get_up_speed_max() < self.total_up_max or self.total_up_max == -1:
                self.total_up_max = test.get_up_speed_max()
            if test.get_down_speed_min() < self.total_down_min or self.total_down_min == -1:
                self.total_down_min = test.get_down_speed_min()
            if test.get_down_speed_max() < self.total_down_max or self.total_down_max == -1:
                self.total_down_max = test.get_down_speed_max()

    def kill_tests(self):
        #only need to kill the last test, since all others will have
        #terminated normally
        kill_failed = False
        try:
            self.tests[-1].kill_subprocess()
        except:
            raise Exception('Killing iperf subprocesses failed.')

if __name__ == '__main__':
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
    parser.add_option('-n', '--num-tests', dest='num_tests', type='int', default=3,
                      help='number of tests to run', metavar='num-tests')
    parser.add_option('', '--csv-file', dest='csvfile', type='string',
                      help='csv filename', metavar='csvfile.csv')
    parser.add_option('', '--summary-file', dest='summaryfile', type='string',
                      help='summary filename', metavar='summaryfile.txt')
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

    multi_test = None
    try:
        csvfile = summaryfile = None
        csvfile_option = parser.get_option('--csv-file')
        summaryfile_option = parser.get_option('--summary-file')
        if not eval('options.' + csvfile_option.dest) == None:
            csvfile = open(options.csvfile, 'a+', 0)
        if not eval('options.' + summaryfile_option.dest) == None:
            summaryfile = open(options.summaryfile, 'a+', 0)

        multi_test = IPerfTestMulti(options.server, description=options.description,
                                    num_tests=options.num_tests, time=options.time,
                                    window=options.window, interval=options.interval,
                                    csvfile=csvfile, summaryfile=summaryfile,
                                    cli=False)
        multi_test.run()
        multi_test.print_summary()
    except KeyboardInterrupt:
        print
        try:
            multi_test.kill_tests()
        except:
            print 'Could not kill the iperf subprocesses, you should do so manually.'
        sys.exit(0)
