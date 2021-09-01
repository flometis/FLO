<?php

function exitSafe($mylog) {
  file_put_contents("deploy.log", $mylog);
  exit;
}

$log = "";

@require("./ip_in_range.php");

//Check IP range

$headers = apache_request_headers();

$ip = "";
if (@$headers["X-Forwarded-For"]) {
            $ips = explode(",",$headers["X-Forwarded-For"]);
                $ip  = $ips[0];
} else {
            $ip = $_SERVER['REMOTE_ADDR'];
}

$ranges = Array();
array_push($ranges, "5.8.113.166/32", "212.237.53.183/32");
$opts = [
  'http' => [
    'method' => 'GET',
    'header' => [
      'User-Agent: PHP'
    ]
  ]
];

$context = stream_context_create($opts);
$github_range = json_decode(file_get_contents("https://api.github.com/meta", false, $context), true)["hooks"];
$ranges = array_merge($ranges, $github_range);

$ip_is_in_range = false;
foreach($ranges as $range) {
  if (ipv4_in_range($ip, $range)) {
    $ip_is_in_range = true;
    break;
  }
}

if (!$ip_is_in_range) {
  header('HTTP/1.1 403 Forbidden');
  //echo "<body>\n";
  //echo "<span style=\"color: #ff0000\">IP ".$ip." not allowed to trigger deploy.</span>\n";
  //echo "</body>\n</html>";
  exitSafe($log);
  $log .= "IP ".$ip." not allowed to trigger deploy.\n";
} else {
  //echo "IP ".$ip." in range";
  $log .= "IP ".$ip." in range.\n";
}

//Check signature

$mySecret = getenv('GITHUB_SECRET', true);
if ($mySecret !== false && $mySecret != "") {
if (!isset($_SERVER['HTTP_X_HUB_SIGNATURE'])) {
  $log .= "Missing HTTP_X_HUB_SIGNATURE.\n";
  exitSafe($log);
}
$githubHeader = $_SERVER['HTTP_X_HUB_SIGNATURE'];
$rawPost = file_get_contents("php://input");
$secret = str_replace("sha1=", "", $githubHeader);
$hash = hash_hmac('sha1', $rawPost, $mySecret);
if (hash_equals($hash, $secret)){
  //echo "<body>\n";
  //echo "<span style=\"color: #ff0000\">Signature invalid.</span>\n";
  //echo "</body>\n</html>";
  $log .= "Signature invalid\n";
  exitSafe($log);
}
} else {
  $log .= "Github Secret not set.\n";
  //echo "GITHUB_SECRET not set, skipping signature verification";
}

//Check user
$github_allowed=getenv('GITHUB_ALLOWED', true);
if ($github_allowed !== false && $github_allowed != "") {
if (!in_array($_POST["pusher"]["name"],explode(",", $github_allowed)) ) {
  //echo "<body>\n";
  //echo "<span style=\"color: #ff0000\">User ".$$_POST["pusher"]["name"]." not allowed to trigger deploy.</span>\n";
  //echo "</body>\n</html>";
  $log .= "User ".$$_POST["pusher"]["name"]." not allowed to trigger deploy.\n";
  exitSafe($log);
} else {
  $log .= "User ".$$_POST["pusher"]["name"]." can deploy.\n";
}
} else {
  $log .= "User check not enabled.\n";
}

//Write file
file_put_contents("deploy.request", strtotime("now"));

$log .= "All checks passed, written deploy.request file.\n";
exitSafe($log);
?>

