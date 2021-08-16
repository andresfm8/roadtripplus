# Test 1 - /
scode=$(curl --write-out %{http_code} --silent --output /dev/null https://sponge-bob.duckdns.org)
if [[ "$scode" -ne 200 ]] ; then
  echo "Test 1 - / There was an error. Status: $scode"
  exit 1
else
  echo "Test 1 - / is OK"
fi
# Test 2 - /health
scode=$(curl --write-out %{http_code} --silent --output /dev/null https://sponge-bob.duckdns.org/health)
if [[ "$scode" -ne 200 ]] ; then
  echo "Test 2 - /health There was an error. Status: $scode"
  exit 1
else
  echo "Test 2 - /health is OK"
fi
# Test 3 - /blog
scode=$(curl --write-out %{http_code} --silent --output /dev/null https://sponge-bob.duckdns.org/blog)
if [[ "$scode" -ne 200 ]] ; then
  echo "Test 4 - /blog There was an error. Status: $scode"
  exit 1
else
  echo "Test 3 - /blog is OK"
fi
# Test 4 - /login
scode=$(curl --write-out %{http_code} --silent --output /dev/null https://sponge-bob.duckdns.org/login)
if [[ "$scode" -ne 200 ]] ; then
  echo "Test 4 - /login There was an error. Status: $scode"
  exit 1
else
  echo "Test 4 - /login is OK"
fi
# Test 5 - /register
scode=$(curl --write-out %{http_code} --silent --output /dev/null https://sponge-bob.duckdns.org/register)
if [[ "$scode" -ne 200 ]] ; then
  echo "Test 5 - /register There was an error. Status: $scode"
  exit 1
else
  echo "Test 5 - /register is OK"
fi

exit 0