# Copyright 2013 The Chromium Authors. All rights reserved.
"""Chromium auto-bisect tool

This script bisects a range of commits using binary search. It starts by getting
reference values for the specified "good" and "bad" commits. Then, for revisions
in between, it will get builds, run tests and classify intermediate revisions as
"good" or "bad" until an adjacent "good" and "bad" revision is found; this is
the culprit.

If the culprit is a roll of a depedency repository (e.g. v8), it will then
expand the revision range and continue the bisect until a culprit revision in
the dependency repository is found.

Example usage using git commit hashes, bisecting a performance test based on
the mean value of a particular metric:

./tools/auto_bisect/bisect_perf_regression.py
  --command "out/Release/performance_ui_tests \
      --gtest_filter=ShutdownTest.SimpleUserQuit"\
  --metric shutdown/simple-user-quit
  --good_revision 1f6e67861535121c5c819c16a666f2436c207e7b\
  --bad-revision b732f23b4f81c382db0b23b9035f3dadc7d925bb\

Example usage using git commit positions, bisecting a functional test based on
whether it passes or fails.

./tools/auto_bisect/bisect_perf_regression.py\
  --command "out/Release/content_unittests -single-process-tests \
            --gtest_filter=GpuMemoryBufferImplTests"\
  --good_revision 408222\
  --bad_revision 408232\
  --bisect_mode return_code\
  --builder_type full

In practice, the auto-bisect tool is usually run on tryserver.chromium.perf
try bots, and is started by tools/run-bisect-perf-regression.py using
config parameters from tools/auto_bisect/bisect.cfg.
import fetch_build
import query_crbug
# regression based on the test results of the initial good and bad revisions.
REGRESSION_CONFIDENCE = 80
# How many times to repeat the test on the last known good and first known bad
# revisions in order to assess a more accurate confidence score in the
# regression culprit.
BORDER_REVISIONS_EXTRA_RUNS = 2
REGRESSION_NOT_REPRODUCED_MESSAGE_TEMPLATE = """
Bisect did not clearly reproduce a regression between the given "good"
and "bad" revisions.

Results:
"Good" revision: {good_rev}
\tMean: {good_mean}
\tStandard error: {good_std_err}
\tSample size: {good_sample_size}
"Bad" revision: {bad_rev}
\tMean: {bad_mean}
\tStandard error: {bad_std_err}
\tSample size: {bad_sample_size}
You may want to try bisecting on a different platform or metric.
"""
PERF_SVN_REPO_URL = 'svn://svn.chromium.org/chrome-try/try-perf'
FULL_SVN_REPO_URL = 'svn://svn.chromium.org/chrome-try/try'
ANDROID_CHROME_SVN_REPO_URL = ('svn://svn.chromium.org/chrome-try-internal/'
                               'try-perf')

def _WaitUntilBuildIsReady(fetch_build_func, builder_name, build_request_id,
                           max_timeout, buildbot_server_url):
    fetch_build_func: Function to check and download build from cloud storage.
    builder_name: Builder bot name on try server.
    buildbot_server_url: Buildbot url to check build status.

    res = fetch_build_func()
            build_request_id, builder_name, buildbot_server_url)
          build_num, builder_name, buildbot_server_url)
    match = re.search(angle_rev_pattern, deps_contents)
    if '--profile-dir' in arg_dict and '--browser' in arg_dict:
      return not bisect_utils.RunProcess(
          [
              'python', path_to_generate,
              '--profile-type-to-generate', profile_type,
              '--browser', arg_dict['--browser'],
              '--output-dir', profile_path
          ])
def _IsRegressionReproduced(known_good_result, known_bad_result):
  """Checks whether the regression was reproduced based on the initial values.
    known_good_result: A dict with the keys "values", "mean" and "std_err".
    known_bad_result: Same as above.
    True if there is a clear change between the result values for the given
    good and bad revisions, False otherwise.
  def PossiblyFlatten(values):
    """Flattens if needed, by averaging the values in each nested list."""
    if isinstance(values, list) and all(isinstance(x, list) for x in values):
      return map(math_utils.Mean, values)
    return values

  p_value = BisectResults.ConfidenceScore(
      PossiblyFlatten(known_bad_result['values']),
      PossiblyFlatten(known_good_result['values']),
      accept_single_bad_or_good=True)

  return p_value > REGRESSION_CONFIDENCE


def _RegressionNotReproducedWarningMessage(
    good_revision, bad_revision, known_good_value, known_bad_value):
  return REGRESSION_NOT_REPRODUCED_MESSAGE_TEMPLATE.format(
      good_rev=good_revision,
      good_mean=known_good_value['mean'],
      good_std_err=known_good_value['std_err'],
      good_sample_size=len(known_good_value['values']),
      bad_rev=bad_revision,
      bad_mean=known_bad_value['mean'],
      bad_std_err=known_bad_value['std_err'],
      bad_sample_size=len(known_bad_value['values']))


  # Create and check out the telemetry-tryjob branch, and edit the configs
  # for the try job there.
def _StartBuilderTryJob(
    builder_type, git_revision, builder_name, job_name, patch=None):
  """Attempts to run a try job from the current directory.
    builder_type: One of the builder types in fetch_build, e.g. "perf".
    git_revision: A git commit hash.
    builder_name: Name of the bisect bot to be used for try job.
    bisect_job_name: Try job name, used to identify which bisect
        job was responsible for requesting a build.
    patch: A DEPS patch (used while bisecting dependency repositories),
        or None if we're bisecting the top-level repository.
  # TODO(prasadv, qyearsley): Make this a method of BuildArchive
  # (which may be renamed to BuilderTryBot or Builder).
    # Temporary branch for running a try job.
    # Create a temporary patch file.
    try_command = [
        'try',
        '--bot=%s' % builder_name,
        '--revision=%s' % git_revision,
        '--name=%s' % job_name,
        '--svn_repo=%s' % _TryJobSvnRepo(builder_type),
        '--diff=%s' % patch_content,
    ]
    print try_command
    output, return_code = bisect_utils.RunGit(try_command)
    command_string = ' '.join(['git'] + try_command)
    if return_code:
      raise RunGitError('Could not execute try job: %s.\n'
                        'Error: %s' % (command_string, output))
                 command_string, output)
    # Delete patch file if exists.
def _TryJobSvnRepo(builder_type):
  """Returns an SVN repo to use for try jobs based on the builder type."""
  if builder_type == fetch_build.PERF_BUILDER:
    return PERF_SVN_REPO_URL
  if builder_type == fetch_build.FULL_BUILDER:
    return FULL_SVN_REPO_URL
  if builder_type == fetch_build.ANDROID_CHROME_PERF_BUILDER:
    return ANDROID_CHROME_SVN_REPO_URL
  raise NotImplementedError('Unknown builder type "%s".' % builder_type)


          if cur_data.get('deps_var') == depot_name:
  def _DownloadAndUnzipBuild(self, revision, depot, build_type='Release',
                             create_patch=False):
      create_patch: Create a patch with any locally modified files.
    if depot not in ('chromium', 'android-chrome'):
      self._CreateDEPSPatch(depot, revision)
      create_patch = True

    if create_patch:
      revision, patch = self._CreatePatch(revision)
    bucket_name, remote_path = fetch_build.GetBucketAndRemotePath(
        revision, builder_type=self.opts.builder_type,
        target_arch=self.opts.target_arch,
        target_platform=self.opts.target_platform,
        deps_patch_sha=deps_patch_sha,
        extra_src=self.opts.extra_src)
    output_dir = os.path.abspath(build_dir)
    fetch_build_func = lambda: fetch_build.FetchFromCloudStorage(
        bucket_name, remote_path, output_dir)

    is_available = fetch_build.BuildIsAvailable(bucket_name, remote_path)
    if is_available:
      return fetch_build_func()

    # When build archive doesn't exist, make a request and wait.
    return self._RequestBuildAndWait(
        revision, fetch_build_func, deps_patch=deps_patch)

  def _RequestBuildAndWait(self, git_revision, fetch_build_func,
                           deps_patch=None):
    """Triggers a try job for a build job.
    This function prepares and starts a try job for a builder, and waits for
    the archive to be produced and archived. Once the build is ready it is
    downloaded.
    For performance tests, builders on the tryserver.chromium.perf are used.
    TODO(qyearsley): Make this function take "builder_type" as a parameter
    and make requests to different bot names based on that parameter.
      git_revision: A git commit hash.
      fetch_build_func: Function to check and download build from cloud storage.
      deps_patch: DEPS patch string, used when bisecting dependency repos.
    if not fetch_build_func:
      return None
        '%s-%s-%s' % (git_revision, deps_patch, time.time()))

    # Revert any changes to DEPS file.
    bisect_utils.CheckRunGit(['reset', '--hard', 'HEAD'], cwd=self.src_cwd)
    builder_name, build_timeout = fetch_build.GetBuilderNameAndBuildTime(
        builder_type=self.opts.builder_type,
        target_arch=self.opts.target_arch,
        target_platform=self.opts.target_platform,
        extra_src=self.opts.extra_src)
      _StartBuilderTryJob(self.opts.builder_type, git_revision, builder_name,
                          job_name=build_request_id, patch=deps_patch)
                   'Error: %s', git_revision, e)
      return None

    # Get the buildbot master URL to monitor build status.
    buildbot_server_url = fetch_build.GetBuildBotUrl(
        builder_type=self.opts.builder_type,
        target_arch=self.opts.target_arch,
        target_platform=self.opts.target_platform,
        extra_src=self.opts.extra_src)

    archive_filename, error_msg = _WaitUntilBuildIsReady(
        fetch_build_func, builder_name, build_request_id, build_timeout,
        buildbot_server_url)
    if not archive_filename:
      logging.warn('%s [revision: %s]', error_msg, git_revision)
    return archive_filename
    The build output directory is wherever the binaries are expected to
    TODO: Simplify and clarify this method if possible.

    output_dir = os.path.join(abs_build_dir, self.GetZipFileBuildDirName())
    logging.info('EXPERIMENTAL RUN, _UnzipAndMoveBuildProducts locals %s',
                 str(locals()))

      logging.info('Extracting "%s" to "%s"', downloaded_file, abs_build_dir)
      fetch_build.Unzip(downloaded_file, abs_build_dir)

  @staticmethod
  def GetZipFileBuildDirName():
    """Gets the base file name of the zip file.

    After extracting the zip file, this is the name of the directory where
    the build files are expected to be. Possibly.

    TODO: Make sure that this returns the actual directory name where the
    Release or Debug directory is inside of the zip files. This probably
    depends on the builder recipe, and may depend on whether the builder is
    a perf builder or full builder.

    Returns:
      The name of the directory inside a build archive which is expected to
      contain a Release or Debug directory.
    """
    if bisect_utils.IsWindowsHost():
      return 'full-build-win32'
    if bisect_utils.IsLinuxHost():
      return 'full-build-linux'
    if bisect_utils.IsMacHost():
      return 'full-build-mac'
    raise NotImplementedError('Unknown platform "%s".' % sys.platform)

    if (self.opts.target_platform in ['chromium', 'android', 'android-chrome']
        and self.opts.builder_type):
      # In case of android-chrome platform, download archives only for
      # android-chrome depot; for other depots such as chromium, v8, skia
      # etc., build the binary locally.
      if self.opts.target_platform == 'android-chrome':
        return depot == 'android-chrome'
      else:
        return (depot == 'chromium' or
                'chromium' in bisect_utils.DEPOT_DEPS_NAME[depot]['from'] or
                'v8' in bisect_utils.DEPOT_DEPS_NAME[depot]['from'])
  def _CreateDEPSPatch(self, depot, revision):
    """Checks out the DEPS file at the specified revision and modifies it.
      if not source_control.CheckoutFileAtRevision(
      if not self.UpdateDeps(revision, depot, deps_file_path):
        raise RuntimeError(
            'Failed to update DEPS file for chromium: [%s]' % chromium_sha)

  def _CreatePatch(self, revision):
    """Creates a patch from currently modified files.

    Args:
      depot: Current depot being bisected.
      revision: A git hash revision of the dependency repository.

    Returns:
      A tuple with git hash of chromium revision and DEPS patch text.
    """
    # Get current chromium revision (git hash).
    chromium_sha = bisect_utils.CheckRunGit(['rev-parse', 'HEAD']).strip()
    if not chromium_sha:
      raise RuntimeError('Failed to determine Chromium revision for %s' %
                         revision)
    # Checkout DEPS file for the current chromium revision.
    diff_command = [
        'diff',
        '--src-prefix=',
        '--dst-prefix=',
        '--no-ext-diff',
        'HEAD',
    ]
    diff_text = bisect_utils.CheckRunGit(diff_command)
    return (chromium_sha, ChangeBackslashToSlashInPatch(diff_text))

  def ObtainBuild(
      self, depot, revision=None, create_patch=False):
      create_patch: Create a patch with any locally modified files.
      build_success = self._DownloadAndUnzipBuild(
          revision, depot, build_type='Release', create_patch=create_patch)
      # Print the current environment set on the machine.
      print 'Full Environment:'
      for key, value in sorted(os.environ.items()):
        print '%s: %s' % (key, value)
      # Print the environment before proceeding with compile.
      sys.stdout.flush()
    # Some "runhooks" calls create symlinks that other (older?) versions
    # do not handle correctly causing the build to fail.  We want to avoid
    # clearing the entire out/ directory so that changes close together will
    # build faster so we just clear out all symlinks on the expectation that
    # the next "runhooks" call will recreate everything properly.  Ignore
    # failures (like Windows that doesn't have "find").
    try:
      bisect_utils.RunProcess(
          ['find', 'out/', '-type', 'l', '-exec', 'rm', '-f', '{}', ';'],
          cwd=self.src_cwd, shell=False)
    except OSError:
      pass
      upload_on_last_run=False, results_label=None, test_run_multiplier=1,
      allow_flakes=True):
      test_run_multiplier: Factor by which to multiply the number of test runs
          and the timeout period specified in self.opts.
      allow_flakes: Report success even if some tests fail to run.
    repeat_count = self.opts.repeat_test_count * test_run_multiplier
    return_codes = []
    for i in xrange(repeat_count):
        if i == self.opts.repeat_test_count - 1 and upload_on_last_run:
        return_codes.append(return_code)
        parsed_metric = _ParseMetricValuesFromOutput(metric, output)
        if parsed_metric:
          metric_values.append(math_utils.Mean(parsed_metric))
        # If there's a failed test, we can bail out early.
        if return_code:
          break
      time_limit = self.opts.max_time_minutes * test_run_multiplier
      if elapsed_minutes >= time_limit:
    overall_success = success_code
    if not allow_flakes and not self._IsBisectModeReturnCode():
      overall_success = (
          success_code
          if (all(current_value == 0 for current_value in return_codes))
              else failure_code)
    return (values, overall_success, output_of_all_runs)
    if 'android' in self.opts.target_platform:
      if not builder.SetupAndroidBuildEnvironment(
          self.opts, path_to_src=self.src_cwd):
    Some commits can be safely skipped (such as a DEPS roll for the repos
    still using .DEPS.git), since the tool is git based those changes
    would have no effect.
    # Skips revisions with DEPS on android-chrome.
    if depot == 'android-chrome':
  def RunTest(self, revision, depot, command, metric, skippable=False,
              skip_sync=False, create_patch=False, force_build=False,
              test_run_multiplier=1):
      skip_sync: Skip the sync step.
      create_patch: Create a patch with any locally modified files.
      force_build: Force a local build.
      test_run_multiplier: Factor by which to multiply the given number of runs
          and the set timeout period.
    if not (self.opts.debug_ignore_sync or skip_sync):
      if not self._SyncRevision(depot, revision, sync_client):
    revision_to_build = revision if not force_build else None
    build_success = self.ObtainBuild(
        depot, revision=revision_to_build, create_patch=create_patch)
    results = self.RunPerformanceTestAndParseResults(
        command, metric, test_run_multiplier=test_run_multiplier)
              time.time() - after_build_time, after_build_time -
              start_build_time)
              BUILD_RESULT_FAIL)
  def _SyncRevision(self, depot, revision, sync_client):
    """Syncs depot to particular revision.
      depot: The depot that's being used at the moment (src, webkit, etc.)
      revision: The revision to sync to.
    self.depot_registry.ChangeToDepotDir(depot)
    if sync_client:
      self.PerformPreBuildCleanup()
    # When using gclient to sync, you need to specify the depot you
    # want so that all the dependencies sync properly as well.
    # i.e. gclient sync src@<SHA1>
    if sync_client == 'gclient' and revision:
      revision = '%s@%s' % (bisect_utils.DEPOT_DEPS_NAME[depot]['src'],
                            revision)
      if depot == 'chromium' and self.opts.target_platform == 'android-chrome':
        return self._SyncRevisionsForAndroidChrome(revision)
    return source_control.SyncToRevision(revision, sync_client)
  def _SyncRevisionsForAndroidChrome(self, revision):
    """Syncs android-chrome and chromium repos to particular revision.

    This is a special case for android-chrome as the gclient sync for chromium
    overwrites the android-chrome revision to TOT. Therefore both the repos
    are synced to known revisions.

    Args:
      revision: Git hash of the Chromium to sync.

    Returns:
      True if successful, False otherwise.
    """
    revisions_list = [revision]
    current_android_rev = source_control.GetCurrentRevision(
        self.depot_registry.GetDepotDir('android-chrome'))
    revisions_list.append(
        '%s@%s' % (bisect_utils.DEPOT_DEPS_NAME['android-chrome']['src'],
                   current_android_rev))
    return not bisect_utils.RunGClientAndSync(revisions_list)
                               known_good_value['std_dev'])
                              known_bad_value['std_dev'])
            revision_info = source_control.QueryRevisionInfo(
                git_revision, cwd=v8_bleeding_edge_dir)
    r1 = self._GetNearestV8BleedingEdgeFromTrunk(
        min_revision_state.revision,
        v8_branch,
        bleeding_edge_branch,
        search_forward=True)
    r2 = self._GetNearestV8BleedingEdgeFromTrunk(
        max_revision_state.revision,
        v8_branch,
        bleeding_edge_branch,
        search_forward=False)
      if ('platform' in bisect_utils.DEPOT_DEPS_NAME[next_depot] and
          bisect_utils.DEPOT_DEPS_NAME[next_depot]['platform'] != os.name):
        continue
    if 'custom_deps' in bisect_utils.DEPOT_DEPS_NAME[current_depot]:
      self.depot_registry.SetDepotDir(
          'v8_bleeding_edge', os.path.join(self.src_cwd, 'v8'))
      self.depot_registry.SetDepotDir(
          'v8', os.path.join(self.src_cwd, 'v8.bak'))
          cmd = [
              'log', '--format=%H', '-1',
              '--before=%d' % (commit_time + 900),
              '--after=%d' % commit_time,
              'origin/master', '--', bisect_utils.FILE_DEPS_GIT
          ]
            self.warnings.append(
                'Detected change to DEPS and modified '
            self.warnings.append(
                'Detected change to DEPS but couldn\'t find '
    # Compare commit timestamp for repos that don't support commit position.
    if not (bad_position and good_position):
      logging.info('Could not get commit positions for revisions %s and %s in '
                   'depot %s', good_position, bad_position, target_depot)
      good_position = source_control.GetCommitTime(good_revision, cwd=cwd)
      bad_position = source_control.GetCommitTime(bad_revision, cwd=cwd)
    1. Non-bisectable revisions for android bots (refer to crbug.com/385324).
    2. Non-bisectable revisions for Windows bots (refer to crbug.com/405274).
  def _GatherResultsFromRevertedCulpritCL(
      self, results, target_depot, command_to_run, metric):
    """Gathers performance results with/without culprit CL.

    Attempts to revert the culprit CL against ToT and runs the
    performance tests again with and without the CL, adding the results to
    the over bisect results.

    Args:
      results: BisectResults from the bisect.
      target_depot: The target depot we're bisecting.
      command_to_run: Specify the command to execute the performance test.
      metric: The performance metric to monitor.
    """
    run_results_tot, run_results_reverted = self._RevertCulpritCLAndRetest(
        results, target_depot, command_to_run, metric)

    results.AddRetestResults(run_results_tot, run_results_reverted)

    if len(results.culprit_revisions) != 1:
      return

    # Cleanup reverted files if anything is left.
    _, _, culprit_depot = results.culprit_revisions[0]
    bisect_utils.CheckRunGit(
        ['reset', '--hard', 'HEAD'],
        cwd=self.depot_registry.GetDepotDir(culprit_depot))

  def _RevertCL(self, culprit_revision, culprit_depot):
    """Reverts the specified revision in the specified depot."""
    if self.opts.output_buildbot_annotations:
      bisect_utils.OutputAnnotationStepStart(
          'Reverting culprit CL: %s' % culprit_revision)
    _, return_code = bisect_utils.RunGit(
        ['revert', '--no-commit', culprit_revision],
        cwd=self.depot_registry.GetDepotDir(culprit_depot))
    if return_code:
      bisect_utils.OutputAnnotationStepWarning()
      bisect_utils.OutputAnnotationStepText('Failed to revert CL cleanly.')
    if self.opts.output_buildbot_annotations:
      bisect_utils.OutputAnnotationStepClosed()
    return not return_code

  def _RevertCulpritCLAndRetest(
      self, results, target_depot, command_to_run, metric):
    """Reverts the culprit CL against ToT and runs the performance test.

    Attempts to revert the culprit CL against ToT and runs the
    performance tests again with and without the CL.

    Args:
      results: BisectResults from the bisect.
      target_depot: The target depot we're bisecting.
      command_to_run: Specify the command to execute the performance test.
      metric: The performance metric to monitor.

    Returns:
      A tuple with the results of running the CL at ToT/reverted.
    """
    # Might want to retest ToT with a revert of the CL to confirm that
    # performance returns.
    if results.confidence < bisect_utils.HIGH_CONFIDENCE:
      return (None, None)

    # If there were multiple culprit CLs, we won't try to revert.
    if len(results.culprit_revisions) != 1:
      return (None, None)

    culprit_revision, _, culprit_depot = results.culprit_revisions[0]

    if not self._SyncRevision(target_depot, None, 'gclient'):
      return (None, None)

    head_revision = bisect_utils.CheckRunGit(['log', '--format=%H', '-1'])
    head_revision = head_revision.strip()

    if not self._RevertCL(culprit_revision, culprit_depot):
      return (None, None)

    # If the culprit CL happened to be in a depot that gets pulled in, we
    # can't revert the change and issue a try job to build, since that would
    # require modifying both the DEPS file and files in another depot.
    # Instead, we build locally.
    force_build = (culprit_depot != target_depot)
    if force_build:
      results.warnings.append(
          'Culprit CL is in another depot, attempting to revert and build'
          ' locally to retest. This may not match the performance of official'
          ' builds.')

    run_results_reverted = self._RunTestWithAnnotations(
        'Re-Testing ToT with reverted culprit',
        'Failed to run reverted CL.',
        head_revision, target_depot, command_to_run, metric, force_build)

    # Clear the reverted file(s).
    bisect_utils.RunGit(
        ['reset', '--hard', 'HEAD'],
        cwd=self.depot_registry.GetDepotDir(culprit_depot))

    # Retesting with the reverted CL failed, so bail out of retesting against
    # ToT.
    if run_results_reverted[1]:
      return (None, None)

    run_results_tot = self._RunTestWithAnnotations(
        'Re-Testing ToT',
        'Failed to run ToT.',
        head_revision, target_depot, command_to_run, metric, force_build)

    return (run_results_tot, run_results_reverted)

  def _RunTestWithAnnotations(
      self, step_text, error_text, head_revision,
      target_depot, command_to_run, metric, force_build):
    """Runs the performance test and outputs start/stop annotations.

    Args:
      results: BisectResults from the bisect.
      target_depot: The target depot we're bisecting.
      command_to_run: Specify the command to execute the performance test.
      metric: The performance metric to monitor.
      force_build: Whether to force a build locally.

    Returns:
      Results of the test.
    """
    if self.opts.output_buildbot_annotations:
      bisect_utils.OutputAnnotationStepStart(step_text)

    # Build and run the test again with the reverted culprit CL against ToT.
    run_test_results = self.RunTest(
        head_revision, target_depot, command_to_run,
        metric, skippable=False, skip_sync=True, create_patch=True,
        force_build=force_build)

    if self.opts.output_buildbot_annotations:
      if run_test_results[1]:
        bisect_utils.OutputAnnotationStepWarning()
        bisect_utils.OutputAnnotationStepText(error_text)
      bisect_utils.OutputAnnotationStepClosed()

    return run_test_results

      return BisectResults(error='Bad rev (%s) appears to be earlier than good '
                                 'rev (%s).' % (good_revision, bad_revision))

      # Abort bisect early when the return codes for known good
      # and known bad revisions are same.
      if (self._IsBisectModeReturnCode() and
          known_bad_value['mean'] == known_good_value['mean']):
        return BisectResults(abort_reason=('known good and known bad revisions '
            'returned same return code (return code=%s). '
            'Continuing bisect might not yield any results.' %
            known_bad_value['mean']))
      if not (self.opts.debug_ignore_regression_confidence or
              self._IsBisectModeReturnCode()):
        if not _IsRegressionReproduced(known_good_value, known_bad_value):
          # If there is no significant difference between "good" and "bad"
          # revision results, then the "bad revision" is considered "good".
          # TODO(qyearsley): Remove this if it is not necessary.
          bad_revision_state.passed = True
          self.warnings.append(_RegressionNotReproducedWarningMessage(
              good_revision, bad_revision, known_good_value, known_bad_value))
                self.warnings.append(
                    'Unfortunately, V8 bisection couldn\'t '
      self._ConfidenceExtraTestRuns(min_revision_state, max_revision_state,
                                    command_to_run, metric)
      results = BisectResults(bisect_state, self.depot_registry, self.opts,
                              self.warnings)

      self._GatherResultsFromRevertedCulpritCL(
          results, target_depot, command_to_run, metric)

      return results
  def _ConfidenceExtraTestRuns(self, good_state, bad_state, command_to_run,
                               metric):
    if (bool(good_state.passed) != bool(bad_state.passed)
       and good_state.passed not in ('Skipped', 'Build Failed')
       and bad_state.passed not in ('Skipped', 'Build Failed')):
      for state in (good_state, bad_state):
        run_results = self.RunTest(
            state.revision,
            state.depot,
            command_to_run,
            metric,
            test_run_multiplier=BORDER_REVISIONS_EXTRA_RUNS)
        # Is extend the right thing to do here?
        if run_results[1] != BUILD_RESULT_FAIL:
          state.value['values'].extend(run_results[0]['values'])
        else:
          warning_text = 'Re-test of revision %s failed with error message: %s'
          warning_text %= (state.revision, run_results[0])
          if warning_text not in self.warnings:
            self.warnings.append(warning_text)

  if os.path.isfile(path_to_dir):
    logging.info('REMOVING FILE %s' % path_to_dir)
    os.remove(path_to_dir)
    self.builder_type = 'perf'
                       help='The highest/lowest percent are discarded to form '
                            'a truncated mean. Values will be clamped to range '
                            '[0, 25]. Default value is 25 percent.')
                       dest='target_arch',
                       choices=['ia32', 'x64', 'arm', 'arm64'],
                            '(default), "x64", "arm" or "arm64".')
                       choices=['Release', 'Debug', 'Release_x64'],
                            '(default), Release_x64 or "Debug".')
    group.add_argument('--builder_type', default=fetch_build.PERF_BUILDER,
                       choices=[fetch_build.PERF_BUILDER,
                                fetch_build.FULL_BUILDER,
                                fetch_build.ANDROID_CHROME_PERF_BUILDER, ''],
                       help='Type of builder to get build from. This '
                            'determines both the bot that builds and the '
                            'place where archived builds are downloaded from. '
                            'For local builds, an empty string can be passed.')
      An instance of argparse.ArgumentParser.
    usage = ('%(prog)s [options] [-- chromium-options]\n'
    if opts.target_arch == 'x64' and opts.target_build_type == 'Release':
      opts.target_build_type = 'Release_x64'
        bisect_printer = BisectPrinter(opts)
        bisect_printer.FormatAndPrintResults(results)