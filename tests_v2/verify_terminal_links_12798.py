import json,os,pathlib,plistlib,shutil,socket,subprocess,sys,time,uuid
app=pathlib.Path(sys.argv[1]); out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
info=plistlib.loads((app/'Contents/Info.plist').read_bytes())
assert info['CFBundleIdentifier']=='com.cmuxterm.app.debug.issue.12798.terminal.links.same',info['CFBundleIdentifier']
exe=app/'Contents/MacOS'/info['CFBundleExecutable']
sock='/tmp/cmux-debug-issue-12798-terminal-links-same.sock'
def read(p):
 try:return json.loads(p.read_text())
 except (OSError,ValueError):return {}
def call(method,**params):
 with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as c:
  c.settimeout(15);c.connect(sock);c.sendall((json.dumps({'id':str(uuid.uuid4()),'method':method,'params':params})+'\n').encode());buf=b''
  while b'\n' not in buf:
   block=c.recv(65536)
   if not block:raise RuntimeError('socket EOF: '+repr(buf))
   buf+=block
 response=json.loads(buf.split(b'\n',1)[0]);assert response.get('ok'),response
 return response['result']
def wait(f,timeout=40):
 deadline=time.monotonic()+timeout;last=None
 while time.monotonic()<deadline:
  try:
   value=f()
   if value:return value
  except Exception as e:last=str(e)
  time.sleep(.15)
 raise AssertionError('Timed out: '+str(last))
def rows(ws):return call('surface.list',workspace_id=ws)['surfaces']
def browsers(ws):return [r for r in rows(ws) if r.get('type')=='browser']
def capture(name):
 time.sleep(.8)
 shot=call('debug.window.screenshot',label=name)
 dst=out/(name+'.png');shutil.copyfile(shot['path'],dst)
 assert dst.stat().st_size>5000
 return dst.name
results=[]
for mode,expected_count in [('split',2),('samePane',1)]:
 fixture=out/(mode+'-fixture');fixture.mkdir(exist_ok=True)
 state=fixture/'state.json';command=fixture/'command.json';command.write_text('{}')
 env=dict(os.environ)
 for k in ['GH_TOKEN','GITHUB_TOKEN','ACTIONS_RUNTIME_TOKEN','ACTIONS_ID_TOKEN_REQUEST_TOKEN','SSH_AUTH_SOCK']:env.pop(k,None)
 env.update(CMUX_TAG='issue-12798-terminal-links-same',CMUX_SOCKET_PATH=sock,CMUX_ALLOW_SOCKET_OVERRIDE='1',CMUX_SOCKET_ENABLE='1',CMUX_SOCKET_MODE='allowAll',CMUX_UI_TEST_MODE='1',CMUX_UI_TEST_TERMINAL_CMD_CLICK_SETUP='1',CMUX_UI_TEST_TERMINAL_CMD_CLICK_PATH=str(state),CMUX_UI_TEST_TERMINAL_CMD_CLICK_COMMAND_PATH=str(command),CMUX_UI_TEST_TERMINAL_CMD_CLICK_FIXTURE_DIR=str(fixture),CMUX_UI_TEST_TERMINAL_CMD_CLICK_LINE_FORMAT='url')
 pathlib.Path(sock).unlink(missing_ok=True)
 log=(out/(mode+'-app.log')).open('w')
 proc=subprocess.Popen([str(exe),'-socketControlMode','allowAll','-browserDisabledOverride','NO','-browserOpenTerminalLinksInCmuxBrowser','YES','-browserInterceptTerminalOpenCommandInCmuxBrowser','YES','-browserTerminalLinkBrowserPlacement',mode,'-NSAppSleepDisabled','YES','-AppleLanguages','(en)'],env=env,stdout=log,stderr=subprocess.STDOUT)
 try:
  wait(lambda:read(state).get('ready')=='1')
  wait(lambda:call('system.ping').get('pong'))
  source=read(state)['surfaceId'];ws=call('workspace.current')['workspace_id']
  before_rows=rows(ws);source_pane=next(r['pane_id'] for r in before_rows if r['id']==source)
  result={'mode':mode,'workspace_id':ws,'source_surface':source,'source_pane':source_pane}
  result['before']=capture(mode+'-before')
  click_id=str(uuid.uuid4());command.write_text(json.dumps({'id':click_id,'action':'stationary_cmd_click_token'}))
  wait(lambda:read(state).get('lastCommandId')==click_id)
  clicked=wait(lambda:browsers(ws) if len(browsers(ws))==1 else None)
  assert len(call('pane.list',workspace_id=ws)['panes'])==expected_count
  assert (clicked[0]['pane_id']==source_pane)==(mode=='samePane')
  result['clicked_browser']=clicked[0];result['after_click']=capture(mode+'-after-click')
  call('surface.focus',workspace_id=ws,surface_id=source)
  output=fixture/'open-output.txt'
  call('surface.send_text',workspace_id=ws,surface_id=source,text="open https://example.com/terminal-placement > '"+str(output)+"' 2>&1")
  call('surface.send_key',workspace_id=ws,surface_id=source,key='enter')
  expected='placement=samePane' if mode=='samePane' else 'placement=reuse'
  wait(lambda:output.exists() and expected in output.read_text())
  opened=wait(lambda:browsers(ws) if len(browsers(ws))==2 else None)
  assert len(call('pane.list',workspace_id=ws)['panes'])==expected_count
  if mode=='samePane':assert all(r['pane_id']==source_pane for r in opened)
  new=next(r for r in opened if r['id']!=clicked[0]['id'])
  call('surface.focus',workspace_id=ws,surface_id=new['id'])
  result['wrapper_output']=output.read_text();result['after_open']=capture(mode+'-after-open')
  if mode=='samePane':
   explicit=call('browser.open_split',workspace_id=ws,surface_id=source,url='about:blank',focus=True)
   assert explicit['created_split'];assert len(call('pane.list',workspace_id=ws)['panes'])==2
   result['manual_split']=explicit;result['after_manual_split']=capture('samePane-manual-split')
  results.append(result);(out/'results.json').write_text(json.dumps(results,indent=2))
  print('PASS',mode,flush=True)
 finally:
  proc.terminate()
  try:proc.wait(timeout=10)
  except subprocess.TimeoutExpired:proc.kill();proc.wait()
  log.close()
print('PASS: clicked URLs, terminal open wrapper, source pane placement and explicit manual splits',flush=True)
