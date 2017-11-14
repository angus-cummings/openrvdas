#!/usr/bin/env python3

import logging
import pprint
import sys
import tempfile
import threading
import time
import unittest
import warnings

sys.path.append('.')

from logger.utils.nmea_parser import NMEAParser

GYR1_RECORDS = """gyr1 2017-11-10:01:00:06.739 $HEHDT,143.7,T*2E
gyr1 2017-11-10:01:00:06.739 $HEROT,-0000.8,A*3E
gyr1 2017-11-10:01:00:07.737 $HEHDT,143.8,T*21
gyr1 2017-11-10:01:00:07.737 $HEROT,0002.9,A*10
gyr1 2017-11-10:01:00:08.737 $HEHDT,143.9,T*20""".split('\n')

GRV1_RECORDS = """grv1 2017-11-10:01:00:06.572 01:024557 00
grv1 2017-11-10:01:00:07.569 01:024106 00
grv1 2017-11-10:01:00:08.572 01:024303 00
grv1 2017-11-10:01:00:09.568 01:024858 00
grv1 2017-11-10:01:00:10.570 01:025187 00
grv1 2017-11-10:01:00:11.571 01:025013 00""".split('\n')

SEAP_RECORDS = """seap 2017-11-04:07:00:39.291859 $PSXN,20,1,0,0,0*3A
seap 2017-11-04:07:00:39.547251 $PSXN,22,0.44,0.74*3A
seap 2017-11-04:07:00:39.802690 $PSXN,23,-1.47,0.01,235.77,-0.38*34
seap 2017-11-04:07:00:41.081670 $PSXN,20,1,0,0,0*3A
seap 2017-11-04:07:00:41.335040 $PSXN,22,0.44,0.74*3A
seap 2017-11-04:07:00:41.590413 $PSXN,23,-1.52,0.05,235.99,-0.39*35
seap 2017-11-04:07:00:31.383319 $GPGGA,002705.69,3938.136133,S,03732.635753,W,1,09,1.0,-5.24,M,,M,,*64
seap 2017-11-04:07:00:33.174207 $GPGGA,002706.69,3938.138360,S,03732.638933,W,1,09,1.0,-4.90,M,,M,,*66
seap 2017-11-04:07:00:34.950267 $GPGGA,002707.69,3938.140620,S,03732.642016,W,1,09,1.0,-4.47,M,,M,,*60
seap 2017-11-04:07:00:36.738001 $GPGGA,002708.69,3938.142856,S,03732.645094,W,1,09,1.0,-4.20,M,,M,,*6E
seap 2017-11-04:07:00:38.525747 $GPGGA,002709.69,3938.144967,S,03732.648274,W,1,09,1.0,-4.14,M,,M,,*6C
seap 2017-11-04:07:00:40.313598 $GPGGA,002710.69,3938.146908,S,03732.651523,W,1,09,1.0,-4.11,M,,M,,*67
seap 2017-11-04:07:00:42.097605 $GPGGA,002711.69,3938.148700,S,03732.654753,W,1,10,0.9,-4.34,M,,M,,*69
seap 2017-11-04:07:00:12.255629 $GPHDT,236.08,T*0A
seap 2017-11-04:07:00:14.043307 $GPHDT,236.17,T*04
seap 2017-11-04:07:00:15.831022 $GPHDT,236.00,T*02
seap 2017-11-04:07:00:17.618759 $GPHDT,235.83,T*0A
seap 2017-11-04:07:00:19.402391 $GPHDT,235.88,T*01
seap 2017-11-04:07:00:21.188320 $GPHDT,236.04,T*06
seap 2017-11-04:07:00:17.363424 $GPVTG,229.08,T,,M,12.2,N,,K,A*23
seap 2017-11-04:07:00:19.151129 $GPVTG,228.96,T,,M,11.8,N,,K,A*2C
seap 2017-11-04:07:00:20.933065 $GPVTG,228.71,T,,M,11.4,N,,K,A*29
seap 2017-11-04:07:00:22.720805 $GPVTG,228.53,T,,M,11.1,N,,K,A*2C
seap 2017-11-04:07:00:24.508455 $GPVTG,228.75,T,,M,11.0,N,,K,A*29
seap 2017-11-04:07:00:32.918751 $GPZDA,002706.69,07,08,2014,,*62
seap 2017-11-04:07:00:34.696982 $GPZDA,002707.69,07,08,2014,,*63
seap 2017-11-04:07:00:36.482615 $GPZDA,002708.69,07,08,2014,,*6C
seap 2017-11-04:07:00:38.270328 $GPZDA,002709.69,07,08,2014,,*6D
seap 2017-11-04:07:00:40.058070 $GPZDA,002710.69,07,08,2014,,*65
seap 2017-11-04:07:00:41.845780 $GPZDA,002711.69,07,08,2014,,*64""".split('\n')

S330_RECORDS = """s330 2017-11-04:05:12:21.511263 $INZDA,000001.17,07,08,2014,,*79
s330 2017-11-04:05:12:21.765827 $INGGA,000001.16,3934.833674,S,03727.698164,W,1,12,0.7,0.03,M,-3.04,M,,*6D
s330 2017-11-04:05:12:22.016470 $INVTG,230.21,T,248.66,M,10.8,N,20.0,K,A*34
s330 2017-11-04:05:12:22.267012 $INRMC,000001.16,A,3934.833674,S,03727.698164,W,10.8,230.21,070814,18.5,W,A*06
s330 2017-11-04:05:12:22.520671 $INHDT,235.50,T*14
s330 2017-11-04:05:12:22.770997 $PSXN,20,1,0,0,0*3A
s330 2017-11-04:05:12:23.022713 $PSXN,22,-0.05,-0.68*32
s330 2017-11-04:05:12:23.274388 $PSXN,23,-2.68,-2.25,235.50,-0.88*1D""".split('\n')

PCOD_RECORDS = """PCOD 2017-11-04:05:12:23.264356 $GPGLL,3934.8363,S,03727.7011,W,000002.125,A*3A
PCOD 2017-11-04:05:12:23.518240 $GPVTG,232.5,T,250.4,M,011.1,N,020.5,K*4D
PCOD 2017-11-04:05:12:23.768523 $GPRMC,000002.125,A,3934.8363,S,03727.7011,W,011.1,232.5,221294,17.8,W*43
PCOD 2017-11-04:05:12:24.018771 $GPZDA,000003.00,22,12,1994,00,00,*4F
PCOD 2017-11-04:05:12:24.274063 $GPZDA,000004.00,22,12,1994,00,00,*48
PCOD 2017-11-04:05:12:24.529377 $GPGGA,000003.125,3934.8376,S,03727.7041,W,1,06,1.4,031.1,M,004.1,M,,*67
PCOD 2017-11-04:05:12:24.782562 $GPGLL,3934.8376,S,03727.7041,W,000003.125,A*3A
PCOD 2017-11-04:05:12:25.034354 $GPVTG,235.4,T,253.2,M,008.8,N,016.2,K*4D
PCOD 2017-11-04:05:12:25.286072 $GPRMC,000003.125,A,3934.8376,S,03727.7041,W,008.8,235.4,221294,17.8,W*44""".split('\n')

GP02_RECORDS = """gp02 2017-11-04:05:12:21.662148 $GPZDA,000003,07,08,2014,7
gp02 2017-11-04:05:12:21.917365 $GPGLL,3934.820,S,03727.675,W
gp02 2017-11-04:05:12:22.168517 $GPVTG,229.9,T,,M,012.1,N,022.4,K
gp02 2017-11-04:05:12:22.422504 $GPZDA,000004,07,08,2014,7
gp02 2017-11-04:05:12:22.675236 $GPGLL,3934.822,S,03727.678,W
gp02 2017-11-04:05:12:22.927688 $GPVTG,229.5,T,,M,012.3,N,022.8,K
gp02 2017-11-04:05:12:23.180968 $GPZDA,000005,07,08,2014,7
gp02 2017-11-04:05:12:23.432572 $GPGLL,3934.822,S,03727.678,W
gp02 2017-11-04:05:12:23.686738 $GPVTG,229.5,T,,M,012.3,N,022.8,K
gp02 2017-11-04:05:12:23.939352 $GPZDA,000006,07,08,2014,7
gp02 2017-11-04:05:12:24.192983 $GPGLL,3934.827,S,03727.686,W
gp02 2017-11-04:05:12:24.448264 $GPVTG,229.8,T,,M,011.9,N,022.1,K
gp02 2017-11-04:05:12:24.702250 $GPZDA,000007,07,08,2014,7
gp02 2017-11-04:05:12:24.953273 $GPGLL,3934.829,S,03727.690,W
gp02 2017-11-04:05:12:25.208551 $GPVTG,230.2,T,,M,011.7,N,021.7,K
gp02 2017-11-04:05:12:25.458579 $GPZDA,000008,07,08,2014,7
gp02 2017-11-04:05:12:25.713710 $GPGLL,3934.831,S,03727.694,W
gp02 2017-11-04:05:12:25.968944 $GPVTG,230.0,T,,M,011.8,N,021.9,K""".split('\n')

ADCP_RECORDS = """adcp 2017-11-04:05:12:21.270191 $PUHAW,UVH,-7.44,-5.15,236.3
adcp 2017-11-04:05:12:21.521661 $PUHAW,UVH,-7.38,-5.27,236.2
adcp 2017-11-04:05:12:21.772433 $PUHAW,UVH,-7.16,-5.40,236.2
adcp 2017-11-04:05:12:22.022646 $PUHAW,UVH,-7.10,-5.36,236.5
adcp 2017-11-04:05:12:22.272873 $PUHAW,UVH,-7.07,-5.27,236.8
adcp 2017-11-04:05:12:22.526512 $PUHAW,UVH,-7.14,-5.25,236.6
adcp 2017-11-04:05:12:22.779671 $PUHAW,UVH,-7.45,-5.35,236.8""".split('\n')

ENG1_RECORDS = """eng1 2017-11-04:05:12:25.553228 12.25 19.70 507.5 569.0 240.5 -751.9 0 0 NAN NAN -11.5 -7.4
eng1 2017-11-04:05:12:25.806867 12.25 19.70 507.5 570.6 240.1 -751.9 0 0 NAN NAN -11.5 -7.4
eng1 2017-11-04:05:12:26.061740 12.25 19.70 507.5 573.8 239.1 -751.9 0 0 NAN NAN -11.5 -7.4
eng1 2017-11-04:05:12:26.314885 12.26 19.70 507.5 566.8 238.4 -751.9 0 0 NAN NAN -11.5 -7.4
eng1 2017-11-04:05:12:26.567011 12.25 19.70 507.5 572.8 239.1 -751.9 0 0 NAN NAN -11.5 -7.4
eng1 2017-11-04:05:12:26.819316 12.25 19.70 507.5 573.8 240.1 -751.9 0 0 NAN NAN -11.5 -7.4
eng1 2017-11-04:05:12:27.072111 12.25 19.70 507.5 571.4 240.2 -751.9 0 0 NAN NAN -11.5 -7.4
eng1 2017-11-04:05:12:27.327319 12.25 19.70 507.5 565.2 239.7 -751.9 0 0 NAN NAN -11.5 -7.4
eng1 2017-11-04:05:12:27.581764 12.25 19.70 507.5 574.4 239.9 -751.9 0 0 NAN NAN -11.5 -7.4
eng1 2017-11-04:05:12:27.832683 12.25 19.70 507.5 574.1 239.7 -751.9 0 0 NAN NAN -11.5 -7.4
eng1 2017-11-04:05:12:28.085470 12.25 19.70 287.1 567.3 239.6 -751.9 0 0 NAN NAN -11.5 -7.4
eng1 2017-11-04:05:12:28.335733 12.25 19.70 507.5 566.0 239.5 -751.9 0 0 NAN NAN -11.5 -7.4""".split('\n')

KNUD_RECORDS = """knud 2017-11-04:05:15:42.994693 3.5kHz,5188.29,0,,,,1500,-39.836439,-37.847002
knud 2017-11-04:05:15:43.250057 3.5kHz,5188.69,0,,,,1500,-39.836743,-37.847468
knud 2017-11-04:05:15:43.500259 3.5kHz,5189.04,0,,,,1500,-39.837049,-37.847935
knud 2017-11-04:05:15:43.753747 3.5kHz,5200.02,0,,,,1500,-39.837358,-37.848386
knud 2017-11-04:05:15:44.005004 3.5kHz,5187.60,0,,,,1500,-39.837664,-37.848836
knud 2017-11-04:05:15:44.260347 3.5kHz,5196.97,1,,,,1500,-39.837938,-37.849228
knud 2017-11-04:05:15:44.515649 3.5kHz,5187.75,0,,,,1500,-39.838243,-37.849672
knud 2017-11-04:05:15:44.770491 3.5kHz,5196.64,0,,,,1500,-39.838544,-37.850118
knud 2017-11-04:05:15:45.021048 3.5kHz,5197.32,0,,,,1500,-39.838852,-37.850564
knud 2017-11-04:05:15:45.276249 3.5kHz,5197.03,0,,,,1500,-39.839154,-37.851016
knud 2017-11-04:05:15:45.531616 3.5kHz,5196.31,0,,,,1500,-39.839419,-37.851429
knud 2017-11-04:05:15:45.786891 3.5kHz,5196.86,0,,,,1500,-39.839719,-37.851894
knud 2017-11-04:05:15:46.042208 3.5kHz,5186.39,0,,,,1500,-39.840014,-37.852360
knud 2017-11-04:05:15:46.297525 3.5kHz,5195.38,0,,,,1500,-39.840306,-37.852828
knud 2017-11-04:05:15:46.552824 3.5kHz,5184.87,0,,,,1500,-39.840605,-37.853298
knud 2017-11-04:05:15:46.803109 3.5kHz,5185.53,0,,,,1500,-39.840907,-37.853764
knud 2017-11-04:05:15:47.058222 3.5kHz,5185.91,0,,,,1500,-39.841175,-37.854183""".split('\n')

def create_file(filename, lines, interval=0, pre_sleep_interval=0):
  time.sleep(pre_sleep_interval)
  logging.info('creating file "%s"', filename)
  f = open(filename, 'w')
  for line in lines:
    time.sleep(interval)
    f.write(line + '\n')
    f.flush()
  f.close()

class TestNMEAParser(unittest.TestCase):

  ############################
  # To suppress resource warnings about unclosed files
  def setUp(self):
    warnings.simplefilter("ignore", ResourceWarning)

  ############################
  def test_default_parser(self):

    p = NMEAParser()
    logging.debug('\n\nMessages: %s', pprint.pformat(p.messages))
    logging.debug('\n\nSensor Models: %s', pprint.pformat(p.sensor_models))
    logging.debug('\n\nMessages: %s', pprint.pformat(p.sensors))

    for records in [
        #GYR1_RECORDS,
        #GRV1_RECORDS,
        #SEAP_RECORDS,
        #S330_RECORDS,
        #PCOD_RECORDS,
        #GP02_RECORDS,
        #ADCP_RECORDS,
        ENG1_RECORDS,
        KNUD_RECORDS
        ]:
      for line in records:
        logging.info('line: %s', line)
        record = p.parse_record(line)
        logging.info('record: %s', str(record))

############################
  def test_parse_records(self):
    p = NMEAParser()

    r = p.parse_record(GYR1_RECORDS[0])
    self.assertEqual(r.data_id, 'gyr1')
    self.assertEqual(r.message_type, '$HEHDT')
    self.assertAlmostEqual(r.timestamp, 1510275606.739)
    self.assertDictEqual(r.fields, {'Gyro1TrueHeading': 143.7})

    r = p.parse_record(GRV1_RECORDS[0])
    self.assertEqual(r.data_id, 'grv1')
    self.assertEqual(r.message_type, '')
    self.assertAlmostEqual(r.timestamp, 1510275606.572)
    self.assertDictEqual(r.fields, {'Grav1Error': 0, 'Grav1ValueMg': 24557})

    r = p.parse_record(SEAP_RECORDS[0])
    self.assertEqual(r.data_id, 'seap')
    self.assertEqual(r.message_type, '$PSXN-20')
    self.assertAlmostEqual(r.timestamp, 1509778839.291859)
    self.assertEqual(r.fields, {'Seap200HeightQual': 0,
                                'Seap200RollPitchQual': 0,
                                'Seap200HorizQual': 1,
                                'Seap200HeadingQual': 0})

    r = p.parse_record(SEAP_RECORDS[1])
    self.assertEqual(r.data_id, 'seap')
    self.assertEqual(r.message_type, '$PSXN-22')
    self.assertAlmostEqual(r.timestamp, 1509778839.547251)
    self.assertEqual(r.fields, {'Seap200GyroOffset': 0.74,
                                'Seap200GyroCal': 0.44})

    r = p.parse_record(SEAP_RECORDS[2])
    self.assertEqual(r.data_id, 'seap')
    self.assertEqual(r.message_type, '$PSXN-23')
    self.assertAlmostEqual(r.timestamp, 1509778839.802690)
    self.assertEqual(r.fields, {'Seap200Roll': -1.47,
                                'Seap200Heading': 235.77,
                                'Seap200Pitch': 0.01})

############################
  def test_parse_nmea(self):
    p = NMEAParser()
    
    (nmea, msg_type) = p.parse_nmea('Gyroscope', GYR1_RECORDS[0].split(' ')[2])
    logging.info('NMEA: %s: %s', msg_type, nmea)
    self.assertEqual(msg_type, '$HEHDT')
    self.assertDictEqual(nmea, {'Checksum': '2E', 'TrueHeading': 143.7})

    (nmea, msg_type) = p.parse_nmea('Gravimeter',
                                    GRV1_RECORDS[0].split(' ', maxsplit=2)[2])
    self.assertEqual(msg_type, '')
    self.assertDictEqual(nmea, {'CounterUnits': 1, 'GravityError': 0,
                                'GravityValueMg': 24557})

    (nmea, msg_type) = p.parse_nmea('Seapath200', SEAP_RECORDS[0].split(' ')[2])
    logging.info('NMEA: %s: %s', msg_type, nmea)
    self.assertEqual(msg_type, '$PSXN-20')
    self.assertDictEqual(nmea, {'HeightQual': 0, 'RollPitchQual': 0,
                                'HorizQual': 1, 'HeadingQual': 0,
                                'Checksum': '3A'})

    (nmea, msg_type) = p.parse_nmea('Seapath200', SEAP_RECORDS[1].split(' ')[2])
    logging.info('NMEA: %s: %s', msg_type, nmea)
    self.assertEqual(msg_type, '$PSXN-22')
    self.assertDictEqual(nmea, {'GyroCal': 0.44, 'GyroOffset': 0.74,
                                'Checksum': '3A'})

    (nmea, msg_type) = p.parse_nmea('Seapath200', SEAP_RECORDS[2].split(' ')[2])
    logging.info('NMEA: %s: %s', msg_type, nmea)
    self.assertEqual(msg_type, '$PSXN-23')
    self.assertDictEqual(nmea, {'Roll': -1.47, 'Heading': 235.77,
                                'Pitch': 0.01, 'Heave': -0.38,
                                'Checksum': '34'})
    
################################################################################
if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('-v', '--verbosity', dest='verbosity',
                      default=0, action='count',
                      help='Increase output verbosity')
  args = parser.parse_args()

  LOGGING_FORMAT = '%(asctime)-15s %(message)s'
  logging.basicConfig(format=LOGGING_FORMAT)

  LOG_LEVELS ={0:logging.WARNING, 1:logging.INFO, 2:logging.DEBUG}
  args.verbosity = min(args.verbosity, max(LOG_LEVELS))
  logging.getLogger().setLevel(LOG_LEVELS[args.verbosity])
  
  #logging.getLogger().setLevel(logging.DEBUG)
  unittest.main(warnings='ignore')
    
