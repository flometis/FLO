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
  exitSafe($log);
  $log .= "IP ".$ip." not allowed to trigger deploy.\n";
} else {
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
//We need application/json, not form-urlencoded
$rawPost = file_get_contents("php://input");
$gitSha = str_replace("sha1=", "", $githubHeader);
$hash = hash_hmac('sha1', $rawPost, $mySecret);
if (!hash_equals($gitSha, $hash)){
  $log .= "Signature invalid\n";
  exitSafe($log);
}
} else {
  $log .= "Github Secret not set.\n";
}

//Check user
$github_allowed=getenv('GITHUB_ALLOWED', true);
$myUser = json_decode($rawPost, true)["pusher"]["name"];
if ($github_allowed !== false && $github_allowed != "") {
if (!in_array($myUser,explode(",", $github_allowed)) ) {
  $log .= "User ".$myUser." not allowed to trigger deploy.\n";
  exitSafe($log);
} else {
  $log .= "User ".$myUser." can deploy.\n";
}
} else {
  $log .= "User check not enabled.\n";
}

//Write file
file_put_contents("deploy.request", strtotime("now"));

$log .= "All checks passed, written deploy.request file.\n";
exitSafe($log);
?>

