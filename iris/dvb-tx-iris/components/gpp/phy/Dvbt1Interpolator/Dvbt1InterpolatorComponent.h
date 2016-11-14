/**
 * \file components/gpp/phy/Dvbt1Interpolator/Dvbt1InterpolatorComponent.h
 * \version 0.1
 *
 * \section COPYRIGHT
 *
 * Copyright 2012-2016 The Iris Project Developers. See the
 * COPYRIGHT file at the top-level directory of this distribution
 * and at http://www.softwareradiosystems.com/iris/copyright.html.
 *
 * \section LICENSE
 *
 * This file is part of the Iris Project.
 *
 * Iris is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 * 
 * Iris is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 * 
 * A copy of the GNU Lesser General Public License can be found in
 * the LICENSE file in the top-level directory of this distribution
 * and at http://www.gnu.org/licenses/.
 *
 * \section DESCRIPTION
 *
 * The Dvbt1Interpolator component.
 */

#ifndef PHY_DVBT1INTERPOLATORCOMPONENT_H_
#define PHY_DVBT1INTERPOLATORCOMPONENT_H_

#include <boost/scoped_ptr.hpp>
#include "irisapi/PhyComponent.h"

/// this defines the memory of the interpolator - keep low to have a good speed
#define T1_RESAMPLE_ORDER 4

namespace iris
{
namespace phy
{

/** A DVB-T1 interpolator component.
 *
 * Dvbt1InterpolatorComponent is the first optional block composing the DVB-T
 * transmission chain. It is required only if the analog conversion module
 * following in the transmission chain has a rate different than that of the
 * natural DVB-T sampling rate (64/7 MHz).
 *
 * The conversion between the input DVB-T sampling rate and the output sampling
 * rate is performed via a very simple sinc-shaped interpolator. The memory of
 * the interpolating response should be kept short, in order to achieve the best
 * processing speed. Clearly, this block distorts the original signal spectrum,
 * and proper actions should be taken to override this detrimental effect.
 * If you have used the DVB-T OFDM modulator previously on the transmission chain,
 * then this effect has already been taken into account and the generated signal
 * spectrum has been linearly predistorted in order to compensate for the 
 * distortion that is generated by the interpolator block.
 *
 * This block accepts in input complex float values and
 * generates in output complex float values.
 *
 * There are parameters several that can be changed in the XML
 * configuration file:
 *
 * * _debug_: by default set to "false", is used to print some small debugging
 *          information for the interested developer.
 * * _insamplerate_: by default set to "0", a placeholder for 64e6/7 Hz. This
 *                   represents the sampling rate of the entering signal.
 *                   **Please note that if you are using the Dvbt1OFDM block,
 *                   then you need to leave this parameter at 0**.
 * * _outsamplerate_: by default set to "0", a placeholder for 64e6/7 Hz. This
 *                    represents the sampling rate adopted by the DAC for
 *                    emitting the BB analog signal
 * * _responsefile_: by default set to "", which means not enabled, this is the 
 *                   name of a text file where
 *                   the impulse response of the interpolating filter
 *                   is saved, line after line.
 *
 * __References__
 * * ETSI Standard: _EN 300 744 V1.5.1, Digital Video Broadcasting (DVB); Framing
 *   structure, channel coding and modulation for digital terrestrial television_,
 *   available at [ETSI Publications Download Area](http://pda.etsi.org/pda/queryform.asp)
 */
class Dvbt1InterpolatorComponent
  : public PhyComponent
{
 public:

  /// A vector of bytes
  typedef std::vector<uint8_t>  ByteVec;
  
  /// An iterator for a vector of bytes
  typedef ByteVec::iterator     ByteVecIt;

  /// A complex type
  typedef std::complex<float>   Cplx;

  /// A vector of complex
  typedef std::vector<Cplx>     CplxVec;

  // An iterator for a vector complex of
  typedef CplxVec::iterator     CplxVecIt;

  /// A vector of float
  typedef std::vector<float>    FloatVec;
  
  /// An iterator for a vector of float
  typedef FloatVec::iterator    FloatVecIt;
  
  /// A vector of integers
  typedef std::vector<int>      IntVec;
  
  /// An iterator for a vector of typedef
  typedef IntVec::iterator      IntVecIt;

  Dvbt1InterpolatorComponent(std::string name);
  ~Dvbt1InterpolatorComponent();
  virtual void calculateOutputTypes(
      std::map<std::string, int>& inputTypes,
      std::map<std::string, int>& outputTypes);
  virtual void registerPorts();
  virtual void initialize();
  virtual void process();
  virtual void parameterHasChanged(std::string name);

 private:

  bool debug_x;               ///< Debug flag (default = false)
  double inSampleRate_x;      ///< Input sampling rate (default = 0) 
  double outSampleRate_x;     ///< Output sampling rate (default = 0) 
  std::string responseFile_x; ///< Text file with impulse response (default = none)

  void setup();
  void destroy();

  double timeStamp_;          ///< Timestamp of current frame
  double sampleRate_;         ///< Sample rate of current frame

  int tiInsize_;              // input basic buffer size
  int tiOutsize_;             // output basic buffer size
  int inOffset_;              // input register offset
  CplxVec inReg_;             // input register
  int inLength_;              // input register length
  IntVec tiBasepointIndex_;   // index of basepoints
  FloatVec tiHI_;             // response stack

  int time_buffer_size(int input_samples);
  int find_rational_approximation(int *num, int *den, double x, int N);
  double *blackman_sinc(int *n_order, double T, double dt, int order);
  double interp_response(double *h, int n, double dt, double t);
  double sinc(double x);

  /// Useful templates
  template <typename T, size_t N>
  static T* begin(T(&arr)[N]) { return &arr[0]; }
  template <typename T, size_t N>
  static T* end(T(&arr)[N]) { return &arr[0]+N; }
};

} // namespace phy
} // namespace iris

#endif // PHY_DVBT1INTERPOLATORCOMPONENT_H_