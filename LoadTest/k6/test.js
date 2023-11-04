import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 30 },
    { duration: '30s', target: 60 },
    { duration: '20s', target: 100 },
  ],
};

export default function () {
  const res = http.get('https://netsys.uno/api/ping');
  check(res, { 'status was 200': (r) => r.status == 200 });
//   sleep(1);
}
